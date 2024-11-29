"""Provide mixin validation class for pattern-based DataGrabber."""

# Authors: Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL


from ..typing import DataGrabberPatterns
from ..utils import logger, raise_error, warn_with_log


__all__ = ["PatternValidationMixin"]


# Define schema for pattern-based datagrabber's patterns
PATTERNS_SCHEMA = {
    "T1w": {
        "mandatory": ["pattern", "space"],
        "optional": {
            "mask": {"mandatory": ["pattern", "space"], "optional": []},
        },
    },
    "T2w": {
        "mandatory": ["pattern", "space"],
        "optional": {
            "mask": {"mandatory": ["pattern", "space"], "optional": []},
        },
    },
    "BOLD": {
        "mandatory": ["pattern", "space"],
        "optional": {
            "mask": {"mandatory": ["pattern", "space"], "optional": []},
            "confounds": {
                "mandatory": ["pattern", "format"],
                "optional": ["mappings"],
            },
            "reference": {"mandatory": ["pattern"], "optional": []},
            "prewarp_space": {"mandatory": [], "optional": []},
        },
    },
    "Warp": {
        "mandatory": ["pattern", "src", "dst", "warper"],
        "optional": {},
    },
    "VBM_GM": {
        "mandatory": ["pattern", "space"],
        "optional": {},
    },
    "VBM_WM": {
        "mandatory": ["pattern", "space"],
        "optional": {},
    },
    "VBM_CSF": {
        "mandatory": ["pattern", "space"],
        "optional": {},
    },
    "DWI": {
        "mandatory": ["pattern"],
        "optional": {},
    },
    "FreeSurfer": {
        "mandatory": ["pattern"],
        "optional": {
            "aseg": {"mandatory": ["pattern"], "optional": []},
            "norm": {"mandatory": ["pattern"], "optional": []},
            "lh_white": {"mandatory": ["pattern"], "optional": []},
            "rh_white": {"mandatory": ["pattern"], "optional": []},
            "lh_pial": {"mandatory": ["pattern"], "optional": []},
            "rh_pial": {"mandatory": ["pattern"], "optional": []},
        },
    },
}


class PatternValidationMixin:
    """Mixin class for pattern validation."""

    def _validate_types(self, types: list[str]) -> None:
        """Validate the types.

        Parameters
        ----------
        types : list of str
            The data types to validate.

        Raises
        ------
        TypeError
            If ``types`` is not a list or if the values are not string.

        """
        if not isinstance(types, list):
            raise_error(msg="`types` must be a list", klass=TypeError)
        if any(not isinstance(x, str) for x in types):
            raise_error(
                msg="`types` must be a list of strings", klass=TypeError
            )

    def _validate_replacements(
        self,
        replacements: list[str],
        patterns: DataGrabberPatterns,
        partial_pattern_ok: bool,
    ) -> None:
        """Validate the replacements.

        Parameters
        ----------
        replacements : list of str
            The replacements to validate.
        patterns : dict
            The patterns to validate replacements against.
        partial_pattern_ok : bool
            Whether to raise error if partial pattern for a data type is found.

        Raises
        ------
        TypeError
            If ``replacements`` is not a list or if the values are not string.
        ValueError
            If a value in ``replacements`` is not part of a data type pattern
            and ``partial_pattern_ok=False`` or
            if no data type patterns contain all values in ``replacements`` and
            ``partial_pattern_ok=False``.

        Warns
        -----
        RuntimeWarning
            If a value in ``replacements`` is not part of the data type pattern
            and ``partial_pattern_ok=True``.

        """
        if not isinstance(replacements, list):
            raise_error(msg="`replacements` must be a list.", klass=TypeError)

        if any(not isinstance(x, str) for x in replacements):
            raise_error(
                msg="`replacements` must be a list of strings",
                klass=TypeError,
            )

        # Make a list of all patterns recursively
        all_patterns = []
        for dtype_val in patterns.values():
            # Conditional for list dtype vals like Warp
            if isinstance(dtype_val, list):
                for entry in dtype_val:
                    all_patterns.append(entry.get("pattern", ""))
            else:
                all_patterns.append(dtype_val.get("pattern", ""))
        # Check for stray replacements
        for x in replacements:
            if all(x not in y for y in all_patterns):
                if partial_pattern_ok:
                    warn_with_log(
                        f"Replacement: `{x}` is not part of any pattern, "
                        "things might not work as expected if you are unsure "
                        "of what you are doing."
                    )
                else:
                    raise_error(
                        msg=f"Replacement: `{x}` is not part of any pattern"
                    )

        # Check that at least one pattern has all the replacements
        at_least_one = False
        for dtype_val in patterns.values():
            # Conditional for list dtype vals like Warp
            if isinstance(dtype_val, list):
                for entry in dtype_val:
                    if all(
                        x in entry.get("pattern", "") for x in replacements
                    ):
                        at_least_one = True
            else:
                if all(
                    x in dtype_val.get("pattern", "") for x in replacements
                ):
                    at_least_one = True
        if not at_least_one and not partial_pattern_ok:
            raise_error(
                msg="At least one pattern must contain all replacements"
            )

    def _validate_mandatory_keys(
        self,
        keys: list[str],
        schema: list[str],
        data_type: str,
        partial_pattern_ok: bool = False,
    ) -> None:
        """Validate mandatory keys.

        Parameters
        ----------
        keys : list of str
            The keys to validate.
        schema : list of str
            The schema to validate against.
        data_type : str
            The data type being validated.
        partial_pattern_ok : bool, optional
            Whether to raise error if partial pattern for a data type is found
            (default True).

        Raises
        ------
        KeyError
            If any mandatory key is missing for a data type and
            ``partial_pattern_ok=False``.

        Warns
        -----
        RuntimeWarning
            If any mandatory key is missing for a data type and
            ``partial_pattern_ok=True``.

        """
        for key in schema:
            if key not in keys:
                if partial_pattern_ok:
                    warn_with_log(
                        f"Mandatory key: `{key}` not found for {data_type}, "
                        "things might not work as expected if you are unsure "
                        "of what you are doing."
                    )
                else:
                    raise_error(
                        msg=f"Mandatory key: `{key}` missing for {data_type}",
                        klass=KeyError,
                    )
            else:
                logger.debug(f"Mandatory key: `{key}` found for {data_type}.")

    def _identify_stray_keys(
        self, keys: list[str], schema: list[str], data_type: str
    ) -> None:
        """Identify stray keys.

        Parameters
        ----------
        keys : list of str
            The keys to check.
        schema : list of str
            The schema to check against.
        data_type : str
            The data type being checked.

        Raises
        ------
        RuntimeError
            If an unknown key is found for a data type.

        """
        for key in keys:
            if key not in schema:
                raise_error(
                    msg=(
                        f"Key: {key} not accepted for {data_type} "
                        "pattern, remove it to proceed"
                    ),
                    klass=RuntimeError,
                )

    def validate_patterns(
        self,
        types: list[str],
        replacements: list[str],
        patterns: DataGrabberPatterns,
        partial_pattern_ok: bool = False,
    ) -> None:
        """Validate the patterns.

        Parameters
        ----------
        types : list of str
            The data types to check patterns of.
        replacements : list of str
            The replacements to be replaced in the patterns.
        patterns : dict
            The patterns to validate.
        partial_pattern_ok : bool, optional
            Whether to raise error if partial pattern for a data type is found.
            If False, a warning is issued instead of raising an error
            (default False).

        Raises
        ------
        TypeError
            If ``patterns`` is not a dictionary.
        ValueError
            If length of ``types`` and ``patterns`` are different or
            if ``patterns`` is missing entries from ``types`` or
            if unknown data type is found in ``patterns`` or
            if data type pattern key contains '*' as value.

        """
        # Validate types
        self._validate_types(types=types)

        # Validate patterns
        if not isinstance(patterns, dict):
            raise_error(msg="`patterns` must be a dict", klass=TypeError)
        # Unequal length of objects
        if len(types) > len(patterns):
            raise_error(
                msg="Length of `types` more than that of `patterns`",
                klass=ValueError,
            )
        # Missing type in patterns
        if any(x not in patterns for x in types):
            raise_error(
                msg="`patterns` must contain all `types`", klass=ValueError
            )
        # Check against schema
        for dtype_key, dtype_val in patterns.items():
            # Check if valid data type is provided
            if dtype_key not in PATTERNS_SCHEMA:
                raise_error(
                    f"Unknown data type: {dtype_key}, "
                    f"should be one of: {list(PATTERNS_SCHEMA.keys())}"
                )
            # Conditional for list dtype vals like Warp
            if isinstance(dtype_val, list):
                for idx, entry in enumerate(dtype_val):
                    # Check mandatory keys for data type
                    self._validate_mandatory_keys(
                        keys=list(entry),
                        schema=PATTERNS_SCHEMA[dtype_key]["mandatory"],
                        data_type=f"{dtype_key}.{idx}",
                        partial_pattern_ok=partial_pattern_ok,
                    )
                    # Check optional keys for data type
                    for optional_key, optional_val in PATTERNS_SCHEMA[
                        dtype_key
                    ]["optional"].items():
                        if optional_key not in entry:
                            logger.debug(
                                f"Optional key: `{optional_key}` missing for "
                                f"{dtype_key}.{idx}"
                            )
                        else:
                            logger.debug(
                                f"Optional key: `{optional_key}` found for "
                                f"{dtype_key}.{idx}"
                            )
                            # Set nested type name for easier access
                            nested_dtype = f"{dtype_key}.{idx}.{optional_key}"
                            nested_mandatory_keys_schema = PATTERNS_SCHEMA[
                                dtype_key
                            ]["optional"][optional_key]["mandatory"]
                            nested_optional_keys_schema = PATTERNS_SCHEMA[
                                dtype_key
                            ]["optional"][optional_key]["optional"]
                            # Check mandatory keys for nested type
                            self._validate_mandatory_keys(
                                keys=list(optional_val["mandatory"]),
                                schema=nested_mandatory_keys_schema,
                                data_type=nested_dtype,
                                partial_pattern_ok=partial_pattern_ok,
                            )
                            # Check optional keys for nested type
                            for (
                                nested_optional_key
                            ) in nested_optional_keys_schema:
                                if (
                                    nested_optional_key
                                    not in optional_val["optional"]
                                ):
                                    logger.debug(
                                        f"Optional key: "
                                        f"`{nested_optional_key}` missing for "
                                        f"{nested_dtype}"
                                    )
                                else:
                                    logger.debug(
                                        f"Optional key: "
                                        f"`{nested_optional_key}` found for "
                                        f"{nested_dtype}"
                                    )
                            # Check stray key for nested data type
                            self._identify_stray_keys(
                                keys=(
                                    optional_val["mandatory"]
                                    + optional_val["optional"]
                                ),
                                schema=(
                                    nested_mandatory_keys_schema
                                    + nested_optional_keys_schema
                                ),
                                data_type=nested_dtype,
                            )
                    # Check stray key for data type
                    self._identify_stray_keys(
                        keys=list(entry.keys()),
                        schema=(
                            PATTERNS_SCHEMA[dtype_key]["mandatory"]
                            + list(
                                PATTERNS_SCHEMA[dtype_key]["optional"].keys()
                            )
                        ),
                        data_type=dtype_key,
                    )
                    # Wildcard check in patterns
                    if "}*" in entry.get("pattern", ""):
                        raise_error(
                            msg=(
                                f"`{dtype_key}.pattern` must not contain `*` "
                                "following a replacement"
                            ),
                            klass=ValueError,
                        )
            else:
                # Check mandatory keys for data type
                self._validate_mandatory_keys(
                    keys=list(dtype_val),
                    schema=PATTERNS_SCHEMA[dtype_key]["mandatory"],
                    data_type=dtype_key,
                    partial_pattern_ok=partial_pattern_ok,
                )
                # Check optional keys for data type
                for optional_key, optional_val in PATTERNS_SCHEMA[dtype_key][
                    "optional"
                ].items():
                    if optional_key not in dtype_val:
                        logger.debug(
                            f"Optional key: `{optional_key}` missing for "
                            f"{dtype_key}."
                        )
                    else:
                        logger.debug(
                            f"Optional key: `{optional_key}` found for "
                            f"{dtype_key}."
                        )
                        # Set nested type name for easier access
                        nested_dtype = f"{dtype_key}.{optional_key}"
                        nested_mandatory_keys_schema = PATTERNS_SCHEMA[
                            dtype_key
                        ]["optional"][optional_key]["mandatory"]
                        nested_optional_keys_schema = PATTERNS_SCHEMA[
                            dtype_key
                        ]["optional"][optional_key]["optional"]
                        # Check mandatory keys for nested type
                        self._validate_mandatory_keys(
                            keys=list(optional_val["mandatory"]),
                            schema=nested_mandatory_keys_schema,
                            data_type=nested_dtype,
                            partial_pattern_ok=partial_pattern_ok,
                        )
                        # Check optional keys for nested type
                        for nested_optional_key in nested_optional_keys_schema:
                            if (
                                nested_optional_key
                                not in optional_val["optional"]
                            ):
                                logger.debug(
                                    f"Optional key: `{nested_optional_key}` "
                                    f"missing for {nested_dtype}"
                                )
                            else:
                                logger.debug(
                                    f"Optional key: `{nested_optional_key}` "
                                    f"found for {nested_dtype}"
                                )
                        # Check stray key for nested data type
                        self._identify_stray_keys(
                            keys=(
                                optional_val["mandatory"]
                                + optional_val["optional"]
                            ),
                            schema=(
                                nested_mandatory_keys_schema
                                + nested_optional_keys_schema
                            ),
                            data_type=nested_dtype,
                        )
                # Check stray key for data type
                self._identify_stray_keys(
                    keys=list(dtype_val.keys()),
                    schema=(
                        PATTERNS_SCHEMA[dtype_key]["mandatory"]
                        + list(PATTERNS_SCHEMA[dtype_key]["optional"].keys())
                    ),
                    data_type=dtype_key,
                )
                # Wildcard check in patterns
                if "}*" in dtype_val.get("pattern", ""):
                    raise_error(
                        msg=(
                            f"`{dtype_key}.pattern` must not contain `*` "
                            "following a replacement"
                        ),
                        klass=ValueError,
                    )

        # Validate replacements
        self._validate_replacements(
            replacements=replacements,
            patterns=patterns,
            partial_pattern_ok=partial_pattern_ok,
        )
