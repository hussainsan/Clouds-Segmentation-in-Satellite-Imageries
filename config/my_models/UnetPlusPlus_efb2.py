config = dict(
    encoder='timm-efficientnet-b2',
    model_network='UnetPlusPlus',
    in_channels=3,
    n_class=1,
    save_path='',
    learning_rate = 0.0003,
    weight_decay = 0.0005,
    seed=10000,
)
config['save_path']='{}_{}'.format(config['encoder'],config['model_network'])