import torch 
import torch.nn as nn
import math
import warnings
import os,sys

def swish(x):
    return x*torch.sigmoid(x)

def getDivisors(n) : 
    divisors = []
    i = 1
    while i <= n : 
        if (n % i==0) : 
            divisors.append(i), 
        i = i + 1
    return divisors


def find_closest_divisor(a,b):
    if a % b == 0:
        return b
    all  = getDivisors(a)
    for idx,val in enumerate(all):
        if b < val:
            if idx == 0:
                return b
            if (val-b)>(b-all[idx-1]):
                return all[idx-1]
            return val
        
def normalize(norm_type,channels,groups):
    if norm_type == 'group':
        if channels % groups != 0:
            groups = find_closest_divisor(channels,groups)
        norm = torch.nn.GroupNorm(groups, channels)
    elif norm_type == 'batch':
        norm = torch.nn.BatchNorm2d(channels)
    else:
        warnings.warn ("Normalization type unknown -> set to None.")
        norm = None

    return norm


def get_timestep_embedding(timesteps, embedding_dim):
    """
    This matches the implementation in Denoising Diffusion Probabilistic Models:
    From Fairseq.
    Build sinusoidal embeddings.
    This matches the implementation in tensor2tensor, but differs slightly
    from the description in Section 3.5 of "Attention Is All You Need".
    """
    assert len(timesteps.shape) == 1

    half_dim = embedding_dim // 2
    emb = math.log(10000) / (half_dim - 1)
    emb = torch.exp(torch.arange(half_dim, dtype=torch.float32) * -emb)
    emb = emb.to(device=timesteps.device)
    emb = timesteps.float()[:, None] * emb[None, :]
    emb = torch.cat([torch.sin(emb), torch.cos(emb)], dim=1)
    if embedding_dim % 2 == 1:  # zero pad
        emb = torch.nn.functional.pad(emb, (0,1,0,0))
    return emb


class conv_block(nn.Module):
    """
    2 convolution layers, with (opt) positional encoding injected in between the 2.
    """
    def __init__(self,in_channels,out_channels,activation = swish,
                 kernel_size=3,padding=1,temb_channels = 512,
                 norm = 'group',gr_norm = 8,dropout=0.0):
        
        super().__init__()
        self.conv1=nn.Conv2d(in_channels,out_channels,kernel_size=kernel_size,padding=padding)
        self.conv2=nn.Conv2d(out_channels,out_channels,kernel_size=kernel_size,padding=padding)
        self.activation = activation
        self.temb_proj = nn.Linear(temb_channels,out_channels)
        if norm is not None:
            self.norm = normalize(norm,out_channels,gr_norm)
        else: 
            self.norm = None
        self.dropout = torch.nn.Dropout(dropout)

    def forward(self, x, temb=None):
        x = self.conv1(x)
        x = self.activation(x)
        x = self.dropout(x)
        if self.norm is not None:
            x = self.norm(x)

        if temb is not None:
            x = x + self.temb_proj(self.activation(temb))[:,:,None,None]

        x = self.conv2(x)
        x = self.activation(x)
        x = self.dropout(x)
        if self.norm is not None:
            x = self.norm(x)

        return x

class downsamp_block(nn.Module):
    """
    Downsamples with strided convolution.
    """
    def __init__(self,in_channels,out_channels,activation = swish,kernel_size=2,
                 padding=0,stride = 2,norm = 'group',gr_norm = 8,dropout=0.0):
        super().__init__()
        self.conv=nn.Conv2d(in_channels,out_channels,kernel_size=kernel_size,padding=padding,stride = stride)
        self.activation = activation
        if norm is not None:
            self.norm = normalize(norm,out_channels,gr_norm)
        else: 
            self.norm = None
        self.dropout = torch.nn.Dropout(dropout)

    def forward(self, x):
        x = self.conv(x)
        x = self.activation(x)
        x = self.dropout(x)
        if self.norm is not None:
            x = self.norm(x)
        return x


class upsamp_block(nn.Module):
    """
    Upsamples with transposed convolution.
    """
    def __init__(self,in_channels,out_channels,activation = swish,kernel_size=2,
                 padding=0,stride = 2,norm = 'group',gr_norm = 8, dropout = 0.0):
        super().__init__()
        self.conv=nn.ConvTranspose2d(in_channels,out_channels,kernel_size=kernel_size,padding=padding,stride = stride)
        self.activation = activation
        if norm is not None:
            self.norm = normalize(norm,out_channels,gr_norm)
        else: 
            self.norm = None
        self.dropout = torch.nn.Dropout(dropout)

    def forward(self, x):
        x = self.conv(x)
        x = self.activation(x)
        x = self.dropout(x)
        if self.norm is not None:
            x = self.norm(x)
        return x



class UNet_PosEncod(nn.Module):
    """
    U-Net implementation with optional upsampling and optional positional encoding.
    Arguments:
      self.in_channels: int, number of input channels
      self.out_channels: int, number of output channels
      self.depth: int, number of downsampling levels.
      !to be completed!
    """

    def __init__(self,UNet_prm:dict,upsampling_factor:int =1,**kwargs):
        
        super().__init__()

        self.norm = UNet_prm.get("norm")
        self.gr_norm = UNet_prm.get("gr_norm")
        self.dropout = UNet_prm.get("dropout")
        self.depth = UNet_prm.get("depth")
        self.feat = UNet_prm.get("feat")
        self.upsampling_factor = upsampling_factor
        self.upsampling_order = UNet_prm.get("upsampling_order")
        self.upsampling_method = UNet_prm.get("upsampling_method")
        self.remove_skip_con = UNet_prm.get("remove_skip_con")
        self.ch = UNet_prm.get("ch",128)
        self.temb_ch = self.ch*4
        self.in_channels = UNet_prm.get("in_channels")
        self.out_channels = UNet_prm.get("out_channels")

        # activation definition
        if UNet_prm.get("activation") == "ReLU":
            self.activation = torch.nn.ReLU()
        elif UNet_prm.get("activation") == "swish": 
            self.activation = swish
        else:
            raise Exception("Activation should be 'ReLU' or 'swish'.")

        # encoder
        self.encoder_conv = nn.ModuleList()
        self.encoder_downsamp = nn.ModuleList()
        for level in range(self.depth): #e.g. self.depth = 3, creating levels: 0,1,2, and level 3 will be the "base" one below.
            if level == 0: 
                in_ch = self.in_channels
                out_ch = self.feat
            else:
                in_ch = self.feat * 2**(level-1)
                out_ch = self.feat * 2**(level) 
            conv_b = conv_block(in_ch,out_ch,activation = self.activation,
                                temb_channels=self.temb_ch,norm = self.norm,
                                gr_norm = self.gr_norm, dropout = self.dropout)
            self.encoder_conv.append(conv_b)
            self.encoder_downsamp.append(downsamp_block(out_ch,out_ch,activation=self.activation,
                                                        stride = 2,norm = self.norm,
                                                        gr_norm = self.gr_norm,
                                                        dropout = self.dropout))


        #base conv block
        self.base = conv_block(self.feat * (2 ** (self.depth-1)), self.feat* 2 ** (self.depth),
                               activation = self.activation,temb_channels=self.temb_ch,
                               norm = self.norm,gr_norm = self.gr_norm,dropout = self.dropout)
            
        #decoder
        self.decoder_upsamp = nn.ModuleList() 
        self.decoder_conv = nn.ModuleList()
        for level in range(0,self.depth): #e.g. self.depth = 3, level 3 is the base and decoder takes care of level: 2,1,0.
            in_ch = self.feat * 2**(level + 1)
            out_ch = self.feat * 2**(level)
            upsamp = upsamp_block (in_ch,out_ch,activation=self.activation,norm=self.norm)
            self.decoder_upsamp.append(upsamp)

            if self.remove_skip_con >= level:
                # If we don't have the skip connections, the convolutional block following
                # the upsampling will have the same number of features in and out
                in_ch = out_ch 
            conv_b = conv_block(in_ch,out_ch,activation = self.activation,temb_channels=self.temb_ch,
                                norm = self.norm,gr_norm = self.gr_norm,dropout = self.dropout)
            self.decoder_conv.append(conv_b)

        # output conv (used only if upsampling before)
        self.out_conv = nn.Conv2d(self.feat, self.out_channels, 1)
        

        #upsampling before
        if self.upsampling_method == 'conv':
            self.upsamp_before = upsamp_block(self.in_channels, self.in_channels, activation=self.activation,
                                               kernel_size=self.upsampling_factor, stride=self.upsampling_factor,
                                               norm = self.norm,gr_norm = 1,dropout = self.dropout)
        else:
            self.upsamp_before = nn.Upsample(scale_factor = self.upsampling_factor,mode=self.upsampling_method)
            
        #upsampling after (+ convolutional block)
        self.upsamp_after = upsamp_block(self.feat,self.feat,activation=self.activation, 
                                         kernel_size=self.upsampling_factor,stride=self.upsampling_factor,
                                         norm = self.norm,gr_norm = self.gr_norm,dropout = self.dropout)
        
        self.upsamp_after_conv = conv_block(self.feat,self.feat,activation = self.activation,
                                            norm = self.norm,gr_norm = self.gr_norm,dropout = self.dropout)

        # timestep embedding
        self.temb = nn.Module()
        self.temb.dense = nn.ModuleList([
            torch.nn.Linear(self.ch,
                            self.temb_ch),
            torch.nn.Linear(self.temb_ch,
                            self.temb_ch),
        ])


    def forward(self, x, t=None):

        if t is not None:
            temb = get_timestep_embedding(t, self.ch)
            temb = self.temb.dense[0](temb)
            temb = self.activation(temb)
            temb = self.temb.dense[1](temb)
        else:
            temb = None

        if self.upsampling_factor > 1 and self.upsampling_order == 'before':
            x = self.upsamp_before(x)

        encoder_out = [] # for skip connections
        for level in range(self.depth): #e.g. self.depth = 3, going through levels 0,1,2
            x = self.encoder_conv[level](x)
            encoder_out.append(x)
            x = self.encoder_downsamp[level](x)

        x = self.base(x) #e.g. self.depth = 3, base is level 3.

        for level in range(self.depth-1,-1,-1): #e.g. self.depth = 3, going through level 2->0
            x = self.decoder_upsamp[level](x)
            if self.remove_skip_con >= level:
                x = self.decoder_conv[level](x)
            else:
                x = self.decoder_conv[level](torch.cat((x, encoder_out[level]), dim=1))

        if self.upsampling_factor > 1 and self.upsampling_order == 'after':
            x = self.upsamp_after(x)
            x = self.upsamp_after_conv(x)
       
        x = self.out_conv(x)
            
        return x
    

