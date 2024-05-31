from PIL import Image
from torchvision import transforms
from embedding.adaclip_modeling.clip import _transform, _convert_image_to_rgb

try:
    from torchvision.transforms import InterpolationMode
    BICUBIC = InterpolationMode.BICUBIC
except ImportError:
    BICUBIC = Image.BICUBIC


def get_transforms(model_name, image_size=None):
    if model_name == "clip":
        return _transform(image_size)
    elif model_name.startswith("mobilenet"):
        preprocess = transforms.Compose([
            transforms.Resize(image_size, interpolation=BICUBIC),
            transforms.CenterCrop(224),
            _convert_image_to_rgb,
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
    elif model_name == "raw":
        preprocess = transforms.Compose([
            transforms.Resize((image_size, image_size), interpolation=BICUBIC),
            _convert_image_to_rgb,
            transforms.Grayscale(),
            transforms.ToTensor(),
        ])
    return preprocess
