import numpy as np

class Intention:
    def __init__(self, num_needs, num_actions, num_inputs, drift_rate=0.01, learning_rate=0.1, noise_scale=0.1):
        self.num_needs = num_needs
        self.num_actions = num_actions
        self.num_inputs = num_inputs
        self.drift_rate = drift_rate
        self.lr = learning_rate
        self.noise_scale = noise_scale

        self.offset_needs = 0
        self.offset_memory = self.offset_needs + num_needs
        self.offset_input_weights = self.offset_memory + num_actions * num_needs
        self.offset_noise = self.offset_input_weights + num_inputs * num_actions
        self.total_states = self.offset_noise + num_actions

        self.chaos_state = np.linspace(0.1, 0.9, self.total_states)

        self.needs = np.zeros(num_needs)
        for i in range(num_needs):
            self.needs[i] = self._chaos_at(self.offset_needs + i)

        self.memory_E = np.zeros((num_actions, num_needs))
        for i in range(num_actions):
            for j in range(num_needs):
                idx = self.offset_memory + i * num_needs + j
                self.memory_E[i, j] = self._chaos_at(idx) * 2 - 1

        self.input_weights = np.zeros((num_inputs, num_actions))
        for i in range(num_inputs):
            for j in range(num_actions):
                idx = self.offset_input_weights + i * num_actions + j
                self.input_weights[i, j] = self._chaos_at(idx) * 0.1

        self.action_effects = np.zeros((num_actions, num_needs))
        for i in range(min(num_actions, num_needs)):
            self.action_effects[i, i] = 0.3
        for i in range(num_actions):
            for j in range(num_needs):
                if self.action_effects[i, j] == 0:
                    self.action_effects[i, j] = 0.1 * ((i + j) % 3)

    def _chaos_at(self, idx):
        self.chaos_state[idx] = 3.9 * self.chaos_state[idx] * (1 - self.chaos_state[idx])
        return self.chaos_state[idx]

    def step(self, input_vector):
        input_vector = np.array(input_vector)

        self.needs = self.needs + self.drift_rate * (1 - self.needs)
        self.needs = np.clip(self.needs, 0, 1)

        noise = np.zeros(self.num_actions)
        for i in range(self.num_actions):
            idx = self.offset_noise + i
            noise[i] = (self._chaos_at(idx) - 0.5) * self.noise_scale

        need_score = np.dot(self.needs, self.memory_E.T)
        input_score = np.dot(input_vector, self.input_weights)
        total_score = need_score + input_score + noise

        action = np.argmax(total_score)

        delta = -self.action_effects[action]
        new_needs = self.needs + delta
        new_needs = np.clip(new_needs, 0, 1)

        reward = -delta

        self.memory_E[action] += self.lr * (reward - self.memory_E[action])

        self.needs = new_needs
        
    def receive_reward(self, action_index, reward):
        self.memory_E[action_index] += self.lr * (reward - self.memory_E[action_index])