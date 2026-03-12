# neural/mlp.py
import random
from .math_ops import MathOps

class MLPClassifier:
    def __init__(self, layers, lr=0.1):
        self.lr = lr
        self.weights = []
        for i in range(len(layers) - 1):
            w = [[random.uniform(-1, 1) for _ in range(layers[i])]
                 for _ in range(layers[i+1])]
            self.weights.append(w)

    def train(self, x, target):
        activations = [x]
        zs = []
        curr = x
        for w in self.weights:
            z = [MathOps.dot(row, curr) for row in w]
            zs.append(z)
            curr = [MathOps.sigmoid(val) for val in z]
            activations.append(curr)

        output = activations[-1]
        deltas = [(output[i] - target[i]) * MathOps.sigmoid_derivative_from_a(output[i])
                  for i in range(len(output))]

        for i in reversed(range(len(self.weights))):
            layer_input = activations[i]
            current_delta = deltas

            if i > 0:
                prev_z = zs[i-1]
                deltas = []
                for j in range(len(self.weights[i][0])):
                    error = sum(current_delta[k] * self.weights[i][k][j]
                                for k in range(len(current_delta)))
                    deltas.append(error * MathOps.sigmoid_derivative(prev_z[j]))

            for r in range(len(self.weights[i])):
                for c in range(len(self.weights[i][0])):
                    self.weights[i][r][c] -= self.lr * current_delta[r] * layer_input[c]