"""
Check the interface to the solver object.

Note:
    These are all aggregate tests, not really testing single units.
"""
from __future__ import absolute_import, division

import unittest
import random

from dwave.cloud.utils import evaluate_ising
from dwave.cloud.config import legacy_load_config
from dwave.cloud.qpu import Client
from dwave.cloud.exceptions import CanceledFutureError
import dwave.cloud.computation


try:
    config_url, config_token, _, config_solver = legacy_load_config()
    if None in [config_url, config_token, config_solver]:
        raise ValueError()
    skip_live = False
except:
    skip_live = True


class PropertyLoading(unittest.TestCase):
    """Ensure that the properties of solvers can be retrieved."""

    @unittest.skipIf(skip_live, "No live server available.")
    def test_load_properties(self):
        """Ensure that the propreties are populated."""
        client = Client(config_url, config_token)
        solver = client.get_solver(config_solver)
        self.assertTrue(len(solver.properties) > 0)

    @unittest.skipIf(skip_live, "No live server available.")
    def test_load_parameters(self):
        """Make sure the parameters are populated."""
        client = Client(config_url, config_token)
        solver = client.get_solver(config_solver)
        self.assertTrue(len(solver.parameters) > 0)

    @unittest.skipIf(skip_live, "No live server available.")
    def test_submit_invalid_parameter(self):
        """Ensure that the parameters are populated."""
        client = Client(config_url, config_token)
        solver = client.get_solver(config_solver)
        assert 'not_a_parameter' not in solver.parameters
        with self.assertRaises(KeyError):
            solver.sample_ising({}, {}, not_a_parameter=True)

    @unittest.skipIf(skip_live, "No live server available.")
    def test_read_connectivity(self):
        """Ensure that the edge set is populated."""
        client = Client(config_url, config_token)
        solver = client.get_solver(config_solver)
        self.assertTrue(len(solver.edges) > 0)


class _QueryTest(unittest.TestCase):
    def _submit_and_check(self, solver, linear, quad, **param):
        results = solver.sample_ising(linear, quad, num_reads=100, **param)

        # Did we get the right number of samples?
        self.assertTrue(100 == sum(results.occurrences))

        # Make sure the number of occurrences and energies are all correct
        for energy, state in zip(results.energies, results.samples):
            self.assertTrue(energy == evaluate_ising(linear, quad, state))

        return results


class Submission(_QueryTest):
    """Submit some sample problems."""

    @unittest.skipIf(skip_live, "No live server available.")
    def test_result_structure(self):
        client = Client(config_url, config_token)
        solver = client.get_solver(config_solver)
        computation = solver.sample_ising({}, {})
        result = computation.result()
        self.assertIn('samples', result)
        self.assertIn('energies', result)
        self.assertIn('occurrences', result)
        self.assertIn('timing', result)

    @unittest.skipIf(skip_live, "No live server available.")
    def test_submit_extra_qubit(self):
        """Submit a defective problem with an unsupported variable."""
        # Connect
        client = Client(config_url, config_token)
        solver = client.get_solver(config_solver)

        # Build a linear problem
        linear = [0] * (max(solver.nodes) + 1)
        for index in solver.nodes:
            linear[index] = 1
        quad = {}

        # Add a variable that shouldn't exist
        linear.append(1)

        with self.assertRaises(ValueError):
            results = solver.sample_ising(linear, quad)
            results.samples

    @unittest.skipIf(skip_live, "No live server available.")
    def test_submit_linear_problem(self):
        """Submit a problem with all the linear terms populated."""
        # Connect
        client = Client(config_url, config_token)
        solver = client.get_solver(config_solver)

        # Build a linear problem
        linear = [0] * (max(solver.nodes) + 1)
        for index in solver.nodes:
            linear[index] = 1
        quad = {}

        # Solve the problem
        self._submit_and_check(solver, linear, quad)

    @unittest.skipIf(skip_live, "No live server available.")
    def test_submit_full_problem(self):
        """Submit a problem with all supported coefficients set."""
        # Connect
        client = Client(config_url, config_token)
        solver = client.get_solver(config_solver)

        # Build a linear problem
        linear = [0] * (max(solver.nodes) + 1)
        for index in solver.nodes:
            linear[index] = random.choice([-1, 1])

        # Build a
        quad = {key: random.choice([-1, 1]) for key in solver.undirected_edges}

        # Solve the problem
        self._submit_and_check(solver, linear, quad)

    @unittest.skipIf(skip_live, "No live server available.")
    def test_submit_dict_problem(self):
        """Submit a problem using a dict for the linear terms."""
        # Connect
        client = Client(config_url, config_token)
        solver = client.get_solver(config_solver)

        # Build a problem
        linear = {index: random.choice([-1, 1]) for index in solver.nodes}
        quad = {key: random.choice([-1, 1]) for key in solver.undirected_edges}

        # Solve the problem
        self._submit_and_check(solver, linear, quad)

    @unittest.skipIf(skip_live, "No live server available.")
    def test_submit_partial_problem(self):
        """Submit a problem with only some of the terms set."""
        # Connect
        client = Client(config_url, config_token)
        solver = client.get_solver(config_solver)

        # Build a linear problem
        linear = [0] * (max(solver.nodes) + 1)
        for index in solver.nodes:
            linear[index] = random.choice([-1, 1])

        # Build a
        quad = {key: random.choice([-1, 1]) for key in solver.undirected_edges}

        # Remove half the qubits
        nodes = list(solver.nodes)
        for index in nodes[0:len(nodes)//2]:
            linear[index] = 0
            quad = {key: value for key, value in quad.items() if index not in key}

        # Solve the problem
        self._submit_and_check(solver, linear, quad)

    @unittest.skipIf(skip_live, "No live server available.")
    def test_submit_batch(self):
        """Submit batch of problems."""
        # Connect
        client = Client(config_url, config_token)
        solver = client.get_solver(config_solver)

        result_list = []
        for _ in range(100):

            # Build a linear problem
            linear = [0] * (max(solver.nodes) + 1)
            for index in solver.nodes:
                linear[index] = random.choice([-1, 1])

            # Build a
            quad = {key: random.choice([-1, 1]) for key in solver.undirected_edges}

            results = solver.sample_ising(linear, quad, num_reads=10)
            result_list.append([results, linear, quad])

        for results, linear, quad in result_list:
            # Did we get the right number of samples?
            self.assertTrue(10 == sum(results.occurrences))

            # Make sure the number of occurrences and energies are all correct
            for energy, state in zip(results.energies, results.samples):
                self.assertTrue(energy == evaluate_ising(linear, quad, state))

    @unittest.skipIf(skip_live, "No live server available.")
    def test_cancel_batch(self):
        """Submit batch of problems, then cancel them."""
        # Connect
        with Client(config_url, config_token) as client:
            solver = client.get_solver(config_solver)

            # Build a linear problem
            linear = [0] * (max(solver.nodes) + 1)
            for index in solver.nodes:
                linear[index] = random.choice([-1, 1])

            # Build a
            quad = {key: random.choice([-1, 1]) for key in solver.undirected_edges}

            result_list = []
            for _ in range(1000):
                results = solver.sample_ising(linear, quad, num_reads=10000)
                result_list.append([results, linear, quad])

            [r[0].cancel() for r in result_list]

            for results, linear, quad in result_list:
                # Responses must be canceled or correct
                try:
                    # Did we get the right number of samples?
                    self.assertTrue(10000 == sum(results.occurrences))

                    # Make sure the number of occurrences and energies are all correct
                    for energy, state in zip(results.energies, results.samples):
                        self.assertTrue(energy == evaluate_ising(linear, quad, state))
                except CanceledFutureError:
                    pass

    @unittest.skipIf(skip_live, "No live server available.")
    def test_wait_many(self):
        """Submit a batch of problems then use `wait_multiple` to wait on all of them."""
        # Connect
        client = Client(config_url, config_token)
        solver = client.get_solver(config_solver)

        # Build a linear problem
        linear = [0] * (max(solver.nodes) + 1)
        for index in solver.nodes:
            linear[index] = random.choice([-1, 1])

        # Build a
        quad = {key: random.choice([-1, 1]) for key in solver.undirected_edges}

        result_list = []
        for _ in range(100):
            results = solver.sample_ising(linear, quad, num_reads=40)
            result_list.append([results, linear, quad])

        dwave.cloud.computation.Future.wait_multiple([f[0] for f in result_list])

        for results, _, _ in result_list:
            self.assertTrue(results.done())

        for results, linear, quad in result_list:
            # Did we get the right number of samples?
            self.assertTrue(40 == sum(results.occurrences))

            # Make sure the number of occurrences and energies are all correct
            for energy, state in zip(results.energies, results.samples):
                self.assertTrue(energy == evaluate_ising(linear, quad, state))

    @unittest.skipIf(skip_live, "No live server available.")
    def test_as_completed(self):
        """Submit a batch of problems then use `as_completed` to iterate over
        all of them."""

        # Connect
        client = Client(config_url, config_token)
        solver = client.get_solver(config_solver)

        # Build a problem
        linear = [0] * (max(solver.nodes) + 1)
        for index in solver.nodes:
            linear[index] = random.choice([-1, 1])
        quad = {key: random.choice([-1, 1]) for key in solver.undirected_edges}

        # Sample the solution 100x40 times
        computations = [solver.sample_ising(linear, quad, num_reads=40) for _ in range(100)]

        # Go over computations, one by one, as they're done and check they're OK
        for computation in dwave.cloud.computation.Future.as_completed(computations):
            self.assertTrue(computation.done())
            self.assertTrue(40 == sum(computation.occurrences))
            for energy, state in zip(computation.energies, computation.samples):
                self.assertTrue(energy == evaluate_ising(linear, quad, state))


class DecodingMethod(_QueryTest):
    """Test different decoding behaviors.

    For now, we will just set the _numpy flag in the future module to control
    how the module acts without it.
    """

    def setUp(self):
        """Reload the future module to undo any changes."""
        from six.moves import reload_module
        reload_module(dwave.cloud.computation)

    @classmethod
    def tearDownClass(cls):
        """Reload the future module to undo any changes."""
        from six.moves import reload_module
        reload_module(dwave.cloud.computation)

    @unittest.skipIf(skip_live, "No live server available.")
    def test_request_matrix_with_no_numpy(self):
        """Submit a problem using a dict for the linear terms."""
        # Connect
        client = Client(config_url, config_token)
        dwave.cloud.computation._numpy = False
        solver = client.get_solver(config_solver)
        solver.return_matrix = True

        # Build a problem
        linear = {index: random.choice([-1, 1]) for index in solver.nodes}
        quad = {key: random.choice([-1, 1]) for key in solver.undirected_edges}

        # Solve the problem
        with self.assertRaises(ValueError):
            self._submit_and_check(solver, linear, quad)

    @unittest.skipIf(skip_live, "No live server available.")
    def test_request_matrix_with_numpy(self):
        """Submit a problem using a dict for the linear terms."""
        # Connect
        import numpy
        client = Client(config_url, config_token)
        assert dwave.cloud.computation._numpy
        solver = client.get_solver(config_solver)
        solver.return_matrix = True

        # Build a problem
        linear = {index: random.choice([-1, 1]) for index in solver.nodes}
        quad = {key: random.choice([-1, 1]) for key in solver.undirected_edges}

        # Solve the problem
        result = self._submit_and_check(solver, linear, quad)
        self.assertIsInstance(result.samples, numpy.ndarray)
        self.assertIsInstance(result.energies, numpy.ndarray)
        self.assertIsInstance(result.occurrences, numpy.ndarray)

    @unittest.skipIf(skip_live, "No live server available.")
    def test_request_list_with_no_numpy(self):
        """Submit a problem using a dict for the linear terms."""
        # Connect
        client = Client(config_url, config_token)
        dwave.cloud.computation._numpy = False
        solver = client.get_solver(config_solver)
        solver.return_matrix = False

        # Build a problem
        linear = {index: random.choice([-1, 1]) for index in solver.nodes}
        quad = {key: random.choice([-1, 1]) for key in solver.undirected_edges}

        # Solve the problem
        self._submit_and_check(solver, linear, quad)

    @unittest.skipIf(skip_live, "No live server available.")
    def test_request_list_with_numpy(self):
        """Submit a problem using a dict for the linear terms."""
        # Connect
        client = Client(config_url, config_token)
        assert dwave.cloud.computation._numpy
        solver = client.get_solver(config_solver)
        solver.return_matrix = False

        # Build a problem
        linear = {index: random.choice([-1, 1]) for index in solver.nodes}
        quad = {key: random.choice([-1, 1]) for key in solver.undirected_edges}

        # Solve the problem
        self._submit_and_check(solver, linear, quad)

    @unittest.skipIf(skip_live, "No live server available.")
    def test_request_raw_matrix_with_no_numpy(self):
        """Submit a problem using a dict for the linear terms."""
        # Connect
        client = Client(config_url, config_token)
        dwave.cloud.computation._numpy = False
        solver = client.get_solver(config_solver)
        solver.return_matrix = True

        # Build a problem
        linear = {index: random.choice([-1, 1]) for index in solver.nodes}
        quad = {key: random.choice([-1, 1]) for key in solver.undirected_edges}

        # Solve the problem
        with self.assertRaises(ValueError):
            self._submit_and_check(solver, linear, quad, answer_mode='raw')

    @unittest.skipIf(skip_live, "No live server available.")
    def test_request_raw_matrix_with_numpy(self):
        """Submit a problem using a dict for the linear terms."""
        # Connect
        import numpy
        client = Client(config_url, config_token)
        assert dwave.cloud.computation._numpy
        solver = client.get_solver(config_solver)
        solver.return_matrix = True

        # Build a problem
        linear = {index: random.choice([-1, 1]) for index in solver.nodes}
        quad = {key: random.choice([-1, 1]) for key in solver.undirected_edges}

        # Solve the problem
        result = self._submit_and_check(solver, linear, quad, answer_mode='raw')
        self.assertIsInstance(result.samples, numpy.ndarray)
        self.assertIsInstance(result.energies, numpy.ndarray)
        self.assertIsInstance(result.occurrences, numpy.ndarray)

    @unittest.skipIf(skip_live, "No live server available.")
    def test_request_raw_list_with_no_numpy(self):
        """Submit a problem using a dict for the linear terms."""
        # Connect
        client = Client(config_url, config_token)
        dwave.cloud.computation._numpy = False
        solver = client.get_solver(config_solver)
        solver.return_matrix = False

        # Build a problem
        linear = {index: random.choice([-1, 1]) for index in solver.nodes}
        quad = {key: random.choice([-1, 1]) for key in solver.undirected_edges}

        # Solve the problem
        self._submit_and_check(solver, linear, quad, answer_mode='raw')

    @unittest.skipIf(skip_live, "No live server available.")
    def test_request_raw_list_with_numpy(self):
        """Submit a problem using a dict for the linear terms."""
        # Connect
        client = Client(config_url, config_token)
        assert dwave.cloud.computation._numpy
        solver = client.get_solver(config_solver)
        solver.return_matrix = False

        # Build a problem
        linear = {index: random.choice([-1, 1]) for index in solver.nodes}
        quad = {key: random.choice([-1, 1]) for key in solver.undirected_edges}

        # Solve the problem
        self._submit_and_check(solver, linear, quad)


if __name__ == '__main__':
    unittest.main()
