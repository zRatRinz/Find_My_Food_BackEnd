import tensorflow as tf
# from tensorflow.keras.layers import BatchNormalization

model = tf.keras.models.load_model(
    "ai/MNV2_Project.keras"
)
print("loaded")


# import tensorflow as tf
# print(tf.__version__)        # 2.13.1
# print(tf.keras.__version__)  # 2.13.x
