"""Provide mixin class for updating metadata."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Union


__all__ = ["UpdateMetaMixin"]


class UpdateMetaMixin:
    """Mixin class for updating meta."""

    def update_meta(
        self,
        input: Union[dict, list[dict]],
        step_name: str,
    ) -> None:
        """Update metadata.

        Parameters
        ----------
        input : dict or list of dict
            The data object to update.
        step_name : str
            The name of the pipeline step.

        """
        # Initialize empty dictionary for the step's metadata
        t_meta = {}
        # Set class name for the step
        t_meta["class"] = self.__class__.__name__
        # Add object variables to metadata if name doesn't start with "_"
        for k, v in vars(self).items():
            if not k.startswith("_"):
                t_meta[k] = v
        # Conditional for list dtype vals like Warp
        if not isinstance(input, list):
            input = [input]
        for entry in input:
            # Add "meta" to the step's entry's local context dict
            if "meta" not in entry:
                entry["meta"] = {}
            # Add step name
            entry["meta"][step_name] = t_meta
            # Add step dependencies
            if "dependencies" not in entry["meta"]:
                entry["meta"]["dependencies"] = set()
            # Update step dependencies
            dependencies = getattr(self, "_DEPENDENCIES", set())
            if dependencies is not None:
                if not isinstance(dependencies, (set, list)):
                    dependencies = {dependencies}
                entry["meta"]["dependencies"].update(dependencies)
