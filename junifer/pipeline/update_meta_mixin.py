"""Provide mixin class for updating metadata."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from .pipeline_component_registry import PipelineComponentRegistry


__all__ = ["UpdateMetaMixin"]


class UpdateMetaMixin:
    """Mixin class for updating meta."""

    def update_meta(
        self,
        input: dict | list[dict],
        step_name: str,
        append: bool = False,
    ) -> None:
        """Update metadata.

        Parameters
        ----------
        input : dict or list of dict
            The data object to update.
        step_name : str
            The name of the pipeline step.
        append : bool, optional
            Whether to append the metadata of the step to a list, for the
            steps that can be several (e.g., the preprocessors), instead of
            replacing the metadata of the previous step (default False).

        """
        # Initialize empty dictionary for the step's metadata
        t_meta = {}
        # Set class name for the step
        t_meta["class"] = self.__class__.__name__
        # Dump model
        t_meta.update(self.model_dump(mode="json"))
        # The parameters set when creating the object and the module to load
        # with `with` to use it (if not built-in), to generate the YAML; they
        # are not part of the MD5 of the features
        fields_set = getattr(self, "_fields_set", None)
        if fields_set is None:
            fields_set = self.model_fields_set
        t_meta["_fields_set"] = sorted(fields_set)
        registering_module = (
            PipelineComponentRegistry().get_registering_module(self.__class__)
        )
        if registering_module is not None:
            t_meta["_with"] = registering_module
        # Conditional for list dtype vals like Warp
        if not isinstance(input, list):
            input = [input]
        for entry in input:
            # Add "meta" to the step's entry's local context dict
            if "meta" not in entry:
                entry["meta"] = {}
            # Add step name
            if append:
                entry["meta"].setdefault(step_name, []).append(t_meta)
            else:
                entry["meta"][step_name] = t_meta
            # Add step dependencies
            if "dependencies" not in entry["meta"]:
                entry["meta"]["dependencies"] = set()
            # Update step dependencies
            dependencies = getattr(self, "_DEPENDENCIES", set())
            if dependencies is not None:
                if not isinstance(dependencies, set | list):
                    dependencies = {dependencies}
                entry["meta"]["dependencies"].update(dependencies)
