# neural/math_ops.py
import math

class MathOps:
    @staticmethod
    def sigmoid(x):
        x = max(-500, min(500, x))
        return 1 / (1 + math.exp(-x))

    @staticmethod
    def sigmoid_derivative(z):
        s = MathOps.sigmoid(z)
        return s * (1 - s)

    @staticmethod
    def sigmoid_derivative_from_a(a):
        return a * (1 - a)

    @staticmethod
    def tanh_derivative(a):
        return 1.0 - a**2

    @staticmethod
    def dot(v1, v2):
        return sum(x * y for x, y in zip(v1, v2))

    @staticmethod
    def softmax(logits):
        max_logit = max(logits)
        exps = [math.exp(l - max_logit) for l in logits]
        sum_exp = sum(exps)
        return [e / sum_exp for e in exps]

    @staticmethod
    def cross_entropy_loss(probs, target_idx):
        return -math.log(probs[target_idx] + 1e-15)

    @staticmethod
    def cross_entropy_grad(logits, target_idx):
        probs = MathOps.softmax(logits)
        grad = probs[:]
        grad[target_idx] -= 1.0
        return grad