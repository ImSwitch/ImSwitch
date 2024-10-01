import json
import pydoc
import torch
from torchvision import transforms
import numpy as np
from pathlib import Path
import os
from imswitch.imcommon.model.dirtools import getSystemUserDir
from imswitch.imcommon.model.logging import initLogger
from imswitch.imreconstruct.model.UNet import UNet_PosEncod
from imswitch.imreconstruct.model.UNetRCAN import UNetRCAN

class Denoiser:
    def __init__(self) -> None:
        self.models_dir = os.path.join(getSystemUserDir(), 'ImSwitchConfig\denoising_models')
        self.__logger = initLogger(self, tryInheritParent=False)
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
            self.__logger.info("Denoising with GPU.")
        else:
            self.device = torch.device("cpu")
            self.__logger.warning("Denoising with cpu, can be slow.")
        self.model = None


    def init_model(self,model_name:str,model_type:str)->None:
        """
        Instantiate model with parameters found in config file of 'model_name'.
        """
        cfg_path = os.path.join(self.models_dir,model_name,"config_train.json")
        try:
            with open(str(cfg_path)) as f:
                cfg_train = json.load(f)
        except FileNotFoundError:
            self.__logger.critical("Model config file not found. Note that name should be 'config_train.json'.")
            return
        
        model_prm = cfg_train.get("model_parameters",None)
        if model_prm is None:
            self.__logger.critical("Model parameters not found in config_train file.")
            return

        if model_type == "UNet":    
            if model_prm.get('UNet_prm',None) is None:
                self.model = UNet_PosEncod(UNet_prm = model_prm)
            else:
                self.model = UNet_PosEncod(**model_prm) #NOTE: will need to add upsampling parameter when necessary!
        elif model_type == "UNetRCAN":
            self.model = UNetRCAN(**model_prm)
        else:
            raise ValueError(f"arg:`model_type` should be one of 'UNet', 'UNetRCAN' but got {model_type} instead.")


    def load_model(self,model_name:str)->None:
        """
        Load state_dict of 'model_best_state_dict.py'.
        """
        sate_dict_path = os.path.join(self.models_dir,model_name, "model_best_state_dict.pt")
        try:
            state_dict = torch.load(sate_dict_path)
        except Exception as e:
            self.__logger.critical(f"Cannot import noise model, got error: {e}")
            return
        
        if self.model is None:
            self.__logger.critical(f"Trying to load state_dict but model instance not existing yet.")
            return

        try:
            self.model.load_state_dict(state_dict['model_state_dict'])
        except Exception as e:
            self.__logger.critical(f"Cannot import state dict, got error: {e}")
            return
    

    def predict(self,data,crop_size,pad=True,clip_neg = True):
        """
        Feeds data into model and returns the prediction.
        Data is center-cropped to crop_size.
        If pad == true, pads prediction with zeros to have the same output size than data.
        """
        
        self.model.to(self.device)
        self.model.eval()

        if len(data.shape) == 2:
            np.expand_dims(data,axis=0)
        
        if crop_size % 16 !=0:
            crop_size = crop_size - crop_size % 16
            self.__logger.info(f"Crop_size rounded to {crop_size}")

        data_tensor = transforms.ToTensor()(np.transpose(data,(1,2,0)))
        data_tensor = transforms.CenterCrop(crop_size)(data_tensor)
        if clip_neg:
            data_tensor = torch.nn.ReLU()(data_tensor)
        
        data_avg = torch.mean(data_tensor)
        data_std = torch.std(data_tensor)
        data_tensor = (data_tensor - data_avg)/data_std

        pred_stack = np.empty((data_tensor.shape[0],data_tensor.shape[1],data_tensor.shape[2]))
        
        for i in range(data_tensor.shape[0]):
            frame = data_tensor[i]
            frame = frame.reshape(1,1,frame.shape[0],frame.shape[1])
            frame = frame.to(self.device)
            prediction = self.model(frame)
            prediction = prediction.cpu().detach().numpy()
            pred_stack[i,...] = prediction

        if pad:
            pad_h = max(int((data.shape[1]-crop_size) // 2),0)
            pad_w = max(int((data.shape[2]-crop_size) // 2),0)
            pad_width = ((0,0),(pad_h,pad_h),(pad_w,pad_w))
            pred_stack = np.pad(pred_stack,pad_width=pad_width,mode='constant', constant_values=0)
        
        return pred_stack
