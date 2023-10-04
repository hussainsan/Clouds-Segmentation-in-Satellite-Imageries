config = dict(
    seed=10000,
    data_path="./data",
    Kfold_index=2,#0,1,2,3,4
    train_image_id_txt_path='',
    val_image_id_txt_path='',
    encoder='timm-efficientnet-b2',
    model_network='DeepLabV3Plus',
    in_channels=3,
    n_class=1,
    save_path='',
    gpu_da=0.25,
    max_epochs = 25,
    train_batch_size = 16,
    test_batch_size = 16,
    lr = 0.0003,
    weight_decay = 0.0005,
    save_inter_epoch = 5,
    print_freq = 50,
    num_workers = 8,
)
config['save_path']='{}_{}_fold_{}'.format(config['encoder'],config['model_network'],config['Kfold_index'])