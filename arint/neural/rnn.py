# neural/rnn.py
import math
import random
from .math_ops import MathOps

class AdvancedRNN:
    def __init__(self, input_dim, hidden_dim, output_dim, activation='tanh'):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        self.activation_name = activation

        def xavier(fan_in, fan_out):
            limit = math.sqrt(6 / (fan_in + fan_out))
            return random.uniform(-limit, limit)

        self.W_xh = [[xavier(input_dim, hidden_dim) for _ in range(input_dim)]
                     for _ in range(hidden_dim)]
        self.W_hh = [[xavier(hidden_dim, hidden_dim) for _ in range(hidden_dim)]
                     for _ in range(hidden_dim)]
        self.W_hy = [[xavier(hidden_dim, output_dim) for _ in range(hidden_dim)]
                     for _ in range(output_dim)]
        self.b_h = [0.0] * hidden_dim
        self.b_y = [0.0] * output_dim

    def _activate(self, x):
        if self.activation_name == 'tanh':
            return math.tanh(x)
        elif self.activation_name == 'sigmoid':
            return MathOps.sigmoid(x)
        return x

    def _activate_derivative(self, a):
        if self.activation_name == 'tanh':
            return 1 - a * a
        elif self.activation_name == 'sigmoid':
            return a * (1 - a)
        return 1.0

    def forward_sequence(self, inputs, h0=None):
        T = len(inputs)
        h = [0.0] * self.hidden_dim if h0 is None else h0[:]
        outputs = []
        hiddens = []
        pre_acts = []

        for t in range(T):
            x = inputs[t]
            z = [0.0] * self.hidden_dim
            for i in range(self.hidden_dim):
                z[i] = (MathOps.dot(self.W_xh[i], x) +
                        MathOps.dot(self.W_hh[i], h) +
                        self.b_h[i])
            pre_acts.append(z)
            h = [self._activate(z[i]) for i in range(self.hidden_dim)]
            hiddens.append(h)
            y = [MathOps.dot(self.W_hy[i], h) + self.b_y[i]
                 for i in range(self.output_dim)]
            outputs.append(y)

        cache = (inputs, hiddens, pre_acts, h0)
        return outputs, hiddens, cache

    def backward_sequence(self, cache, d_outputs, lr=0.01):
        inputs, hiddens, pre_acts, h0 = cache
        T = len(inputs)

        dW_xh = [[0.0] * self.input_dim for _ in range(self.hidden_dim)]
        dW_hh = [[0.0] * self.hidden_dim for _ in range(self.hidden_dim)]
        dW_hy = [[0.0] * self.hidden_dim for _ in range(self.output_dim)]
        db_h = [0.0] * self.hidden_dim
        db_y = [0.0] * self.output_dim
        d_h_next = [0.0] * self.hidden_dim

        for t in reversed(range(T)):
            d_y = d_outputs[t]
            h_t = hiddens[t]

            for i in range(self.output_dim):
                for j in range(self.hidden_dim):
                    dW_hy[i][j] += d_y[i] * h_t[j]
                db_y[i] += d_y[i]

            d_h = [0.0] * self.hidden_dim
            for j in range(self.hidden_dim):
                d_h[j] = sum(d_y[i] * self.W_hy[i][j] for i in range(self.output_dim))

            for j in range(self.hidden_dim):
                d_h[j] += d_h_next[j]

            d_z = [d_h[i] * self._activate_derivative(h_t[i]) for i in range(self.hidden_dim)]

            x_t = inputs[t]
            h_prev = hiddens[t-1] if t > 0 else (h0 or [0.0]*self.hidden_dim)
            for i in range(self.hidden_dim):
                for j in range(self.input_dim):
                    dW_xh[i][j] += d_z[i] * x_t[j]
                for j in range(self.hidden_dim):
                    dW_hh[i][j] += d_z[i] * h_prev[j]
                db_h[i] += d_z[i]

            d_h_next = [0.0] * self.hidden_dim
            for j in range(self.hidden_dim):
                d_h_next[j] = sum(d_z[i] * self.W_hh[i][j] for i in range(self.hidden_dim))

        for i in range(self.hidden_dim):
            for j in range(self.input_dim):
                self.W_xh[i][j] -= lr * dW_xh[i][j]
            for j in range(self.hidden_dim):
                self.W_hh[i][j] -= lr * dW_hh[i][j]
            self.b_h[i] -= lr * db_h[i]

        for i in range(self.output_dim):
            for j in range(self.hidden_dim):
                self.W_hy[i][j] -= lr * dW_hy[i][j]
            self.b_y[i] -= lr * db_y[i]