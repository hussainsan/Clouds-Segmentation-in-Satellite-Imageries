import numpy as np
import tifffile
import albumentations as A
from torch.utils.data import Dataset
from albumentations.pytorch import ToTensorV2
import glob
import pandas as pd
from sklearn.model_selection import train_test_split
import re
import os
def prepare_datasets():
    """
    Prepare training and validation datasets.

    Returns:
        train_set, valid_set: The prepared training and validation datasets.
    """

    # Retrieve paths for image and mask data
    PATH_IMGS = glob.glob('./data/train_true_color/train_true_color_*.tif')
    PATH_MASKS = glob.glob('./data/train_mask/train_mask_*.tif')

    # Function to extract the numerical identifier from filename
    def extract_number(filepath):
        # Extract number from the filename using regular expression
        match = re.search(r'(\d+)', filepath)
        if match:
            return int(match.group(1))
        return -1  # return a default value if no number is found

    # Sort file paths based on numerical identifier
    PATH_IMGS = sorted(PATH_IMGS, key=extract_number)
    PATH_MASKS = sorted(PATH_MASKS, key=extract_number)

    # Create a DataFrame with image and mask paths
    dataset = pd.DataFrame({
        'image_path': PATH_IMGS,
        'mask_path': PATH_MASKS
    })
    
    # Check through the dataset to ensure that each image and its corresponding mask share the same identifier
    for _, row in dataset.iterrows():
        # Extract the base filename without extension
        img_name = os.path.splitext(os.path.basename(row['image_path']))[0].replace('train_true_color_', '')
        mask_name = os.path.splitext(os.path.basename(row['mask_path']))[0].replace('train_mask_', '')
        
        # Check if the identifiers match
        assert img_name == mask_name, f"Mismatch found: {img_name} and {mask_name}"
        
    print("head dataset ", dataset.head())
    print("dataset shape ",dataset.shape)
    # dataset = dataset.iloc[:100]

    # Split dataset into training and validation subsets
    train_df, valid_df = train_test_split(dataset, test_size=0.2, random_state=42)

    # Assume LoadDataset and DataTransform are defined elsewhere in your code
    train_set = LoadDataset(train_df, 'train', transform=DataTransform())
    valid_set = LoadDataset(valid_df, 'valid', transform=DataTransform())

    print("Training set size: ", len(train_set))
    print("Validation set size: ", len(valid_set))

    return train_set, valid_set


class DataTransform():
	"""
	A class used to transform datasets.

	Attributes:
		data_transform (dict): Contains the transformation operations for different phases (e.g. "train").

	Methods:
		__call__(phase, img, mask=None): Transforms the given image and mask based on the specified phase.

	Usage:
		transform = DataTransform()
		transformed_data = transform("train", img, mask)
	"""
	def __init__(self):
		self.data_transform = {
			"train": A.Compose(
				[
					A.RandomRotate90(p=0.5),
					A.HorizontalFlip(p=0.5),
                    A.VerticalFlip(p=0.5),
                    A.Transpose(p=0.5),
					A.RandomResizedCrop(512, 512, interpolation=1, p=1),
					ToTensorV2(),
				]
			),
        
            "valid": A.Compose(
				[
					A.Resize(512, 512, interpolation=1, p=1),
					ToTensorV2(),
				]
			),
			"test": A.Compose(
				[
					A.Resize(512, 512, interpolation=1, p=1),
					ToTensorV2(),
				]
			)
		}

	def __call__(self, phase, img, mask=None):
		if mask is None:
			return self.data_transform[phase](image=img)
		else:
			transformed = self.data_transform[phase](image=img, mask=mask)
			return transformed

class LoadDataset(Dataset):
    def __init__(self, df, phase, transform):
        """
        Args:
            df (DataFrame): DataFrame containing file paths. Must have 'image_path' column. If masks are present, it should also have 'mask_path'.
            phase (str): One of train, valid, test.
            transform (DataTransform): Transformation class.
        """
        self.df = df
        self.phase = phase
        self.transform = transform

    def __len__(self):
        return len(self.df)
    
    def get_dataframe(self):
        """Method to return the internal DataFrame."""
        return self.df
    
    def __getitem__(self, index):
        row = self.df.iloc[index]
        
        img_path = row['image_path']
        img = tifffile.imread(img_path).astype(np.float32) 
        img = np.clip(img, 400, 2400) / 2400
        
        if self.phase == 'test':
            img = self.transform(self.phase, img)["image"]
            return img
        else:
            mask_path = row['mask_path']
            mask = tifffile.imread(mask_path).astype(np.float32)

            if self.phase == 'train':
                transformed = self.transform(self.phase, img, mask)
                return transformed['image'], transformed['mask']
            
            elif self.phase == 'valid':
                transformed = self.transform(self.phase, img, mask)
                return transformed['image'], transformed['mask']
