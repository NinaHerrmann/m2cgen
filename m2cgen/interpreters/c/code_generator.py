from contextlib import contextmanager
import re
from m2cgen.interpreters.code_generator import CLikeCodeGenerator, CodeTemplate


class CCodeGenerator(CLikeCodeGenerator):
    tpl_scalar_var_declare = CodeTemplate("double {var_name};")
    tpl_vector_var_declare = CodeTemplate("double {var_name}[{size}];")

    scalar_type = "double"
    vector_type = "double *"

    def add_function_def(self, name, args, is_scalar_output):
        return_type = self.scalar_type if is_scalar_output else "void"

        func_args = ", ".join([
            f"{self._get_var_declare_type(is_vector)} {n}"
            for is_vector, n in args])
        function_def = f"{return_type} {name}({func_args}) {{"
        self.add_code_line(function_def)
        self.increase_indent()

    @contextmanager
    def function_definition(self, name, args, is_scalar_output):
        self.add_function_def(name, args, is_scalar_output)
        yield
        self.add_block_termination()

    def add_var_declaration(self, size):
        var_name = self.get_var_name()

        if size > 1:
            tpl = self.tpl_vector_var_declare
        else:
            tpl = self.tpl_scalar_var_declare

        self.add_code_line(tpl(var_name=var_name, size=size))
        return var_name

    def add_var_assignment(self, var_name, value, value_size):
        if value_size == 1:
            return super().add_var_assignment(var_name, value, value_size)

        # vectors require special handling since we can't just assign
        # vectors in C.
        self.add_assign_array_statement(value, var_name, value_size)

    def add_assign_array_statement(self, source_var, target_var, size):
        if size < 2:
            matches = re.findall(r'var(\d+)', source_var)
            self.add_code_line(f"output[0] = var{matches[0]};")
            exit()

        for i in range(size):
            matches = re.findall(r'var(\d+)', source_var)
            self.add_code_line(f"output[{i}] = var{matches[0]}[{i}];")

    def add_dependency(self, dep):
        self.prepend_code_line(f"#include {dep}")

    def vector_init(self, values):
        self.add_code_line(f"{self.scalar_type} intermediate{0}[{len(values)}];")
        counter = 0
        for v in values:
            self.add_code_line(f"intermediate{0}[{counter}] = {v};")
            counter = counter + 1
        name = f"intermediate{0}"
        return name

    def _get_var_declare_type(self, is_vector):
        return self.vector_type if is_vector else self.scalar_type
