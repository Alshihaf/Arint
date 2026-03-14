
# core/neural_network.py
# Implementasi Jaringan Saraf modular dari nol dengan backpropagation.
import math
import random
import json

# --- Fungsi Aktivasi dan Turunannya ---

def sigmoid(x):
    """Fungsi aktivasi sigmoid."""
    # Menambahkan pengecekan untuk menghindari overflow
    if x < -700:
        return 0.0
    return 1 / (1 + math.exp(-x))

def sigmoid_derivative(x):
    """Turunan dari fungsi sigmoid."""
    s = sigmoid(x)
    return s * (1 - s)

def relu(x):
    """Fungsi aktivasi Rectified Linear Unit (ReLU)."""
    return max(0, x)

def relu_derivative(x):
    """Turunan dari fungsi ReLU."""
    return 1 if x > 0 else 0

def tanh(x):
    """Fungsi aktivasi hyperbolic tangent."""
    return math.tanh(x)

def tanh_derivative(x):
    """Turunan dari fungsi tanh."""
    return 1 - math.tanh(x)**2

# --- Fungsi Loss ---

def mse_loss(predicted, actual):
    """Mean Squared Error loss."""
    return sum([(p - a)**2 for p, a in zip(predicted, actual)]) / len(predicted)

def mse_loss_derivative(predicted, actual):
    """Turunan dari Mean Squared Error loss."""
    return [2 * (p - a) for p, a in zip(predicted, actual)]


class DenseLayer:
    """Lapisan Dense (fully-connected) yang mampu melakukan forward dan backward pass."""
    def __init__(self, input_size, output_size, activation='''relu'''):
        self.input_size = input_size
        self.output_size = output_size
        self.weights = [[random.uniform(-0.5, 0.5) for _ in range(input_size)] for _ in range(output_size)]
        self.biases = [random.uniform(-0.5, 0.5) for _ in range(output_size)]
        self.activation_str = activation.lower()

        # Pilih fungsi aktivasi dan turunannya
        if self.activation_str == '''sigmoid''':
            self.activation = sigmoid
            self.activation_derivative = sigmoid_derivative
        elif self.activation_str == '''tanh''':
            self.activation = tanh
            self.activation_derivative = tanh_derivative
        else: # Default ke ReLU
            self.activation = relu
            self.activation_derivative = relu_derivative
            
        # Variabel untuk menyimpan state selama forward pass untuk digunakan di backward pass
        self.inputs = []
        self.z = [] # Output sebelum aktivasi

    def forward(self, inputs):
        """Melakukan forward pass dan menyimpan state untuk backward pass."""
        self.inputs = inputs
        self.z = []
        outputs = []
        for i in range(self.output_size):
            net_input = sum(inputs[j] * self.weights[i][j] for j in range(self.input_size)) + self.biases[i]
            self.z.append(net_input)
            outputs.append(self.activation(net_input))
        return outputs

    def backward(self, d_loss_d_output):
        """Melakukan backward pass (backpropagation) untuk menghitung gradien."""
        d_loss_d_z = [d_loss_d_output[i] * self.activation_derivative(self.z[i]) for i in range(self.output_size)]
        
        self.d_loss_d_weights = [[0]*self.input_size for _ in range(self.output_size)]
        self.d_loss_d_biases = [0]*self.output_size
        d_loss_d_input = [0]*self.input_size

        for i in range(self.output_size):
            # Gradien untuk bobot
            for j in range(self.input_size):
                self.d_loss_d_weights[i][j] = d_loss_d_z[i] * self.inputs[j]
            
            # Gradien untuk bias
            self.d_loss_d_biases[i] = d_loss_d_z[i]

            # Gradien untuk input lapisan sebelumnya
            for j in range(self.input_size):
                d_loss_d_input[j] += self.weights[i][j] * d_loss_d_z[i]
                
        return d_loss_d_input

    def update(self, learning_rate):
        """Memperbarui bobot dan bias menggunakan gradien yang dihitung."""
        for i in range(self.output_size):
            for j in range(self.input_size):
                self.weights[i][j] -= learning_rate * self.d_loss_d_weights[i][j]
            self.biases[i] -= learning_rate * self.d_loss_d_biases[i]


class ModularNeuralNetwork:
    """Jaringan Saraf modular yang mendukung pelatihan melalui backpropagation."""
    def __init__(self):
        self.layers = []
        print("Modular Neural Network with backpropagation initialized.")

    def add_layer(self, layer: DenseLayer):
        self.layers.append(layer)

    def predict(self, inputs):
        current_outputs = inputs
        for layer in self.layers:
            current_outputs = layer.forward(current_outputs)
        return current_outputs

    def train(self, X_train, y_train, epochs, learning_rate):
        """Melatih jaringan menggunakan dataset yang diberikan."""
        print(f"Starting training for {epochs} epochs with learning rate {learning_rate}...")
        for epoch in range(epochs):
            total_loss = 0
            for x, y_true in zip(X_train, y_train):
                # Forward pass
                y_pred = self.predict(x)
                
                # Hitung loss
                total_loss += mse_loss(y_pred, y_true)
                
                # Backward pass
                d_loss = mse_loss_derivative(y_pred, y_true)
                
                # Propagasi error ke belakang melalui semua lapisan
                for layer in reversed(self.layers):
                    d_loss = layer.backward(d_loss)
            
                # Perbarui bobot
                for layer in self.layers:
                    layer.update(learning_rate)

            # Tampilkan loss rata-rata setiap beberapa epoch
            if (epoch + 1) % 100 == 0:
                avg_loss = total_loss / len(X_train)
                print(f'Epoch {epoch + 1}/{epochs}, Loss: {avg_loss:.6f}')
        print("Training complete.")

    def save_weights(self, path):
        """Menyimpan bobot dan bias jaringan ke file JSON."""
        model_data = {
            "layers": [
                {
                    "weights": layer.weights,
                    "biases": layer.biases,
                    "activation": layer.activation_str
                } for layer in self.layers
            ]
        }
        with open(path, 'w') as f:
            json.dump(model_data, f, indent=4)
        print(f"Model weights saved to {path}")

    def load_weights(self, path):
        """Memuat bobot dan bias jaringan dari file JSON."""
        with open(path, 'r') as f:
            model_data = json.load(f)
        
        if len(self.layers) != len(model_data["layers"]):
            raise ValueError("Arsitektur jaringan yang dimuat tidak cocok dengan arsitektur saat ini.")

        for i, layer_data in enumerate(model_data["layers"]):
            self.layers[i].weights = layer_data["weights"]
            self.layers[i].biases = layer_data["biases"]
        print(f"Model weights loaded from {path}")


# --- Contoh Penggunaan: Melatih Jaringan untuk Masalah XOR ---

if __name__ == '''__main__''':
    # Data training untuk XOR
    X_train = [[0, 0], [0, 1], [1, 0], [1, 1]]
    y_train = [[0], [1], [1], [0]]

    # 1. Buat instance jaringan
    xor_net = ModularNeuralNetwork()

    # 2. Tentukan arsitektur (input 2 -> hidden 3 -> output 1)
    # Menggunakan tanh karena cocok untuk output antara -1 dan 1, tetapi sigmoid juga berfungsi
    xor_net.add_layer(DenseLayer(2, 3, activation='''tanh'''))
    xor_net.add_layer(DenseLayer(3, 1, activation='''tanh'''))

    # 3. Latih jaringan
    xor_net.train(X_train, y_train, epochs=2000, learning_rate=0.1)

    # 4. Uji jaringan setelah pelatihan
    print("\n--- Testing after training ---")
    for x in X_train:
        prediction = xor_net.predict(x)
        # Output dari tanh adalah antara -1 dan 1, kita bulatkan ke 0 atau 1
        final_prediction = 1 if prediction[0] > 0 else 0
        print(f"Input: {x}, Prediction: {prediction[0]:.4f}, Result: {final_prediction}")

    # 5. Simpan bobot yang telah dilatih
    # xor_net.save_weights("xor_model.json")

    # # 6. Buat jaringan baru dan muat bobot untuk verifikasi
    # new_xor_net = ModularNeuralNetwork()
    # new_xor_net.add_layer(DenseLayer(2, 3, activation='''tanh'''))
    # new_xor_net.add_layer(DenseLayer(3, 1, activation='''tanh'''))
    # new_xor_net.load_weights("xor_model.json")
    
    # print("\n--- Testing loaded model ---")
    # for x in X_train:
    #     prediction = new_xor_net.predict(x)
    #     final_prediction = 1 if prediction[0] > 0 else 0
    #     print(f"Input: {x}, Prediction: {prediction[0]:.4f}, Result: {final_prediction}")
