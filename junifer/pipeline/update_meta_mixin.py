"""Provide mixin class for updating metadata."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from typing import Dict


class UpdateMetaMixin:
    """Mixin class for updating meta."""

    def update_meta(
        self,
        input: Dict,
        step_name: str,
    ) -> None:
        """Update metadata.

        Parameters
        ----------
        input : dict
            The data object to update.
        step_name : str
            The name of the pipeline step.
        """
        t_meta = {}
        t_meta["class"] = self.__class__.__name__
        for k, v in vars(self).items():
            if not k.startswith("_"):
                t_meta[k] = v

        if "meta" not in input:
            input["meta"] = {}
        input["meta"][step_name] = t_meta
        if "dependencies" not in input["meta"]:
            input["meta"]["dependencies"] = set()

        dependencies = getattr(self, "_DEPENDENCIES", set())
        if dependencies is not None:
            if not isinstance(dependencies, (set, list)):
                dependencies = set([dependencies])
            input["meta"]["dependencies"].update(dependencies)
