import numpy as np
from mytorch import tensor
from mytorch.tensor import Tensor
from mytorch.nn.module import Module
from mytorch.nn.activations import Tanh, ReLU, Sigmoid
from mytorch.nn.util import PackedSequence, pack_sequence, unpack_sequence


class RNNUnit(Module):
    """
    This class defines a single RNN Unit block.

    Args:
        input_size (int): # features in each timestep
        hidden_size (int): # features generated by the RNNUnit at each timestep
        nonlinearity (string): Non-linearity to be applied the result of matrix operations 
    """

    def __init__(self, input_size, hidden_size, nonlinearity="tanh"):

        super(RNNUnit, self).__init__()

        # Initializing parameters
        self.weight_ih = Tensor(
            np.random.randn(hidden_size, input_size),
            requires_grad=True,
            is_parameter=True,
        )
        self.bias_ih = Tensor(
            np.zeros(hidden_size), requires_grad=True, is_parameter=True
        )
        self.weight_hh = Tensor(
            np.random.randn(hidden_size, hidden_size),
            requires_grad=True,
            is_parameter=True,
        )
        self.bias_hh = Tensor(
            np.zeros(hidden_size), requires_grad=True, is_parameter=True
        )

        self.hidden_size = hidden_size

        # Setting the Activation Unit
        if nonlinearity == "tanh":
            self.act = Tanh()
        elif nonlinearity == "relu":
            self.act = ReLU()

    def __call__(self, input, hidden=None):
        return self.forward(input, hidden)

    def forward(self, x, hidden=None):
        """
        Args:
            input (Tensor): (effective_batch_size,input_size)
            hidden (Tensor,None): (effective_batch_size,hidden_size)
        Return:
            Tensor: (effective_batch_size,hidden_size)
        """

        # TODO: INSTRUCTIONS
        # Perform matrix operations to construct the intermediary value from input and hidden tensors
        # Apply the activation on the resultant
        # Remeber to handle the case when hidden = None. Construct a tensor of appropriate size, filled with 0s to use as the hidden.
        # note to self: formaula is given below
        # h0t = tanh(weight_ih*input + bias_ih + weight_hh*hidden + bias_hh)
        if not (type(x) == Tensor):
            raise Exception(f"Input must be Tensor. Got {type(x)}")

        if not hidden:
            hidden_shape = (x.shape[0], self.hidden_size)
            hidden = Tensor(
                np.zeros(hidden_shape), requires_grad=True, is_parameter=True,
            )

        weighted_sum = (x @ self.weight_ih.T() + self.bias_ih) + (
            (hidden @ self.weight_hh.T()) + self.bias_hh
        )
        weight_hprime = self.act(weighted_sum)
        return weight_hprime


class TimeIterator(Module):
    """
    For a given input this class iterates through time by processing the entire
    seqeunce of timesteps. Can be thought to represent a single layer for a 
    given basic unit which is applied at each time step.
    
    Args:
        basic_unit (Class): RNNUnit or GRUUnit. This class is used to instantiate the unit that will be used to process the inputs
        input_size (int): # features in each timestep
        hidden_size (int): # features generated by the RNNUnit at each timestep
        nonlinearity (string): Non-linearity to be applied the result of matrix operations 

    """

    def __init__(self, basic_unit, input_size, hidden_size, nonlinearity="tanh"):
        super(TimeIterator, self).__init__()

        # basic_unit can either be RNNUnit or GRUUnit
        self.unit = basic_unit(input_size, hidden_size, nonlinearity)

    def __call__(self, input, hidden=None):
        return self.forward(input, hidden)

    def forward(self, input, hidden=None):

        """
        NOTE: Please get a good grasp on util.PackedSequence before attempting this.

        Args:
            input (PackedSequence): input.data is tensor of shape ( total number of timesteps (sum) across all samples in the batch, input_size)
            hidden (Tensor, None): (batch_size, hidden_size)
        Returns:
            PackedSequence: ( total number of timesteps (sum) across all samples in the batch, hidden_size)
            Tensor (batch_size,hidden_size): This is the hidden generated by the last time step for each sample joined together. Samples are ordered in descending order based on number of timesteps. This is a slight deviation from PyTorch.
        """

        # Resolve the PackedSequence into its components
        data, sorted_indices, batch_sizes = input

        # TODO: INSTRUCTIONS
        # Iterate over appropriate segments of the "data" tensor to pass same timesteps across all samples in the batch simultaneously to the unit for processing.
        # Remeber to account for scenarios when effective_batch_size changes between one iteration to the next
        # index_counter = 0
        X = []
        start = 0
        end = 0
        # retrieve samples per timestep
        for i in range(len(batch_sizes)):
            end = start + batch_sizes[i]
            timestep_data = data[start:end]
            X.append(timestep_data)
            start = end
        hidden_states = [0 for x in X]
        hidden_step_per_batch = []
        last_hidden_step_per_sample = []
        for i in range(len(X)):
            hidden_state = None
            if i == 0:
                h_previous = hidden
                # hidden_state == self.unit.forward(X[i], hidden)
            else:
                effective_batch_size = X[i].shape[0]
                h_previous = hidden_states[i - 1][:effective_batch_size]
            hidden_state = self.unit.forward(X[i], h_previous)

            hidden_states[i] = hidden_state
            hidden_step_per_batch.append(hidden_state[None, -1, :])

        # Get hidden generated by the last time step for each sample joined together.
        # Samples are ordered in descending order based on number of timesteps
        batch_size_sample_count = {x: None for x in set(batch_sizes)}
        for i in range(len(batch_sizes)):
            key = batch_sizes[i]
            batch_size_sample_count[key] = i
        target_hidden_step_indices = sorted(batch_size_sample_count.values())
        last_hidden_step_per_sample = [
            hidden_step_per_batch[i] for i in target_hidden_step_indices
        ]
        last_hidden_step_per_sample.reverse()

        # return packed sequence and hidden timesteps
        ps = PackedSequence(
            data=tensor.cat(hidden_states),
            sorted_indices=sorted_indices,
            batch_sizes=batch_sizes,
        )
        return ps, tensor.cat(last_hidden_step_per_sample)


class RNN(TimeIterator):
    """
    Child class for TimeIterator which appropriately initializes the parent class to construct an RNN.
    Args:
        input_size (int): # features in each timestep
        hidden_size (int): # features generated by the RNNUnit at each timestep
        nonlinearity (string): Non-linearity to be applied the result of matrix operations 
    """

    def __init__(self, input_size, hidden_size, nonlinearity="tanh"):
        # TODO: Properly Initialize the RNN class
        raise NotImplementedError("Initialize properly!")

