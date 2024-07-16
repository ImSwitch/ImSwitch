import torch 
import torch.nn as nn

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
        norm = None

    return norm

class conv_block(nn.Module):
    """
    2 convolution layers.
    """
    def __init__(self,in_channels,out_channels,activation = swish,
                 kernel_size=3,padding=1,norm = 'group',
                 gr_norm = 8,dropout=0.0):
        
        super().__init__()
        self.conv1=nn.Conv2d(in_channels,out_channels,kernel_size=kernel_size,padding=padding)
        self.conv2=nn.Conv2d(out_channels,out_channels,kernel_size=kernel_size,padding=padding)
        self.activation = activation
        if norm is not None:
            self.norm = normalize(norm,out_channels,gr_norm)
        else: 
            self.norm = None
        self.dropout = torch.nn.Dropout(dropout)

    def forward(self, x):
        x = self.conv1(x)
        x = self.activation(x)
        x = self.dropout(x)

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
    

class ChannelAttention(nn.Module):
    def __init__(self, num_features, reduction):
        super().__init__()
        self.module = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Conv2d(num_features, num_features // reduction, kernel_size=1),
            nn.LeakyReLU(inplace=True),
            nn.Conv2d(num_features // reduction, num_features, kernel_size=1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return x * self.module(x)


class RCAB(nn.Module):
    def __init__(self, num_features, reduction):
        super().__init__()
        self.module = nn.Sequential(
            nn.Conv2d(num_features, num_features, kernel_size=3, padding=1),
            nn.LeakyReLU(inplace=True),
            nn.Conv2d(num_features, num_features, kernel_size=3, padding=1),
            ChannelAttention(num_features, reduction)
        )

    def forward(self, x):
        return x+self.module(x)


class RG(nn.Module):
    def __init__(self, num_features, num_rcab, reduction,dropout=0):
        super().__init__()
        self.module = [RCAB(num_features, reduction) for _ in range(num_rcab)]
        self.module.append(nn.Conv2d(num_features, num_features, kernel_size=3, padding=1))
        self.module = nn.Sequential(*self.module)
        self.dropout = torch.nn.Dropout(dropout)

    def forward(self, x):
        x = x + self.module(x)
        x = self.dropout(x)
        return x


class RCAN(nn.Module):
    def __init__(self, num_features = 1, num_rg = 3, num_rcab = 8, reduction = 4,dropout=0):
        super().__init__()
        self.sf = nn.Conv2d(2, num_features, kernel_size=3, padding=1)
        self.rgs = nn.Sequential(*[RG(num_features, num_rcab, reduction,dropout) for _ in range(num_rg)])
        self.conv1 = nn.Conv2d(num_features, num_features, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(num_features, 1, kernel_size=3, padding=1)

    def forward(self, x):
        x = self.sf(x)
        residual = x
        x = self.rgs(x)
        x = self.conv1(x)
        x += residual
        x = self.conv2(x)
        return x


class UNet(nn.Module):
    """
    U-Net implementation, with possiblity to changed skip connectino for CAB.
    NOTE: compared to unet in "UNet_posEncod.py", I removed, at least for now:
         - upsampling
         - pos. encoding
         - remove skip connection option

    Arguments:
      in_channels: int, number of input channels
      out_channels: int, number of output channels
      depth: int, number of downsampling levels.
      !to be completed!
    """

    def __init__(self, 
                 in_channels=1, 
                 out_channels=1, 
                 depth=3, 
                 feat=8, 
                 cab_skip_con = False,
                 cab_reduction = 4,
                 activation="swish",
                 norm = 'group',
                 gr_norm = 8,
                 dropout = 0,
                 **kwargs
                 ):
        
        super().__init__()

        assert depth > 0, "Cannot do a UNet with depth < 1!"

        self.norm = norm
        self.gr_norm = gr_norm
        self.dropout = dropout
        self.depth = depth
        self.feat = feat
        self.cab_skip_con = cab_skip_con

        # activation definition
        if activation == "ReLU":
            self.activation = torch.nn.ReLU()
        elif activation == "swish": 
            self.activation = swish
        else:
            raise Exception("Activation should be 'ReLU' or 'swish'.")

        # encoder
        self.encoder_conv = nn.ModuleList()
        self.encoder_downsamp = nn.ModuleList()
        if self.cab_skip_con:
            self.cab_skip_list = nn.ModuleList() 

        for level in range(depth): #e.g. depth = 3, creating levels: 0,1,2, and level 3 will be the "base" one below.
            if level == 0: 
                in_ch = in_channels
                out_ch = self.feat
            else:
                in_ch = feat * 2**(level-1)
                out_ch = feat * 2**(level) 
            conv_b = conv_block(in_ch,out_ch,activation = self.activation,norm = self.norm,
                                gr_norm = self.gr_norm, dropout = self.dropout)
            self.encoder_conv.append(conv_b)
            self.encoder_downsamp.append(downsamp_block(out_ch,out_ch,activation=self.activation,
                                                        stride = 2,norm = self.norm,
                                                        gr_norm = self.gr_norm,
                                                        dropout = self.dropout))
            if self.cab_skip_con:
                self.cab_skip_list.append(RCAB(num_features=out_ch,reduction=cab_reduction))


        #base conv block
        self.base = conv_block(feat * (2 ** (depth-1)), feat* 2 ** (depth),
                               activation = self.activation, norm = self.norm,
                               gr_norm = self.gr_norm,dropout = self.dropout)
            
        #decoder
        self.decoder_upsamp = nn.ModuleList() 
        self.decoder_conv = nn.ModuleList()
        for level in range(0,depth): #e.g. depth = 3, level 3 is the base and decoder takes care of level: 2,1,0.
            in_ch = feat * 2**(level + 1)
            out_ch = feat * 2**(level)
            upsamp = upsamp_block (in_ch,out_ch,activation=self.activation,norm=self.norm)
            self.decoder_upsamp.append(upsamp)

            conv_b = conv_block(in_ch,out_ch,activation = self.activation,
                                norm = self.norm,gr_norm = self.gr_norm,dropout = self.dropout)
            self.decoder_conv.append(conv_b)


        # output convolution
        self.out_conv = nn.Conv2d(self.feat, out_channels, 1)
        

    def forward(self, x):

        encoder_out = [] # for skip connections
        for level in range(self.depth): #e.g. depth = 3, going through levels 0,1,2
            x = self.encoder_conv[level](x)
            encoder_out.append(x)
            x = self.encoder_downsamp[level](x)

        x = self.base(x) #e.g. depth = 3, base is level 3.

        for level in range(self.depth-1,-1,-1): #e.g. depth = 3, going through level 2->0
            x = self.decoder_upsamp[level](x)
            if self.cab_skip_con:
                skip = self.cab_skip_list[level](encoder_out[level])
            else:
                skip = encoder_out[level]

            x = self.decoder_conv[level](torch.cat((x, skip), dim=1))
       
        x = self.out_conv(x)
            
        return x
    

class UNetRCAN(nn.Module):
    """
    UNet + RCAN implementation.
    NOTE:
        - activation choice for now only on unet. Maybe could be added one some parts of RCAN too later.
        - normalization only applied to unet -> need to check where to add it exactly for RCAN
        => check original rcan code for that, it is included in there.
        - no upsampling for now. But it will need to be added for upsampling task, and 
        with some options: before unet, after unet, after RCAN...

    """
    def __init__(self, UNet_prm:dict,RCAN_prm:dict,upsampling_factor:int=1,**kwargs):
        
        super().__init__()
        self.unet = UNet(**UNet_prm)
        self.rcan = RCAN(**RCAN_prm)

    def forward(self, input_tensor,*args):
        x = input_tensor
        y_unet = self.unet(x)
        y = torch.cat([y_unet, x],dim=1)
        y = self.rcan(y)
        return y
