"""Provides a mixin to emit FutureWarnings for deprecated camelCase attributes."""
import warnings


class _DeprecatedAliasesMixin:  # pylint: disable=too-few-public-methods
    """
    Mixin that maps legacy camelCase names to new snake_case attributes,
    emitting a FutureWarning at use.
    """

    _ALIASES: dict[str, str] = {
        "tokenId": "token_id",
        "totalSupply": "total_supply",
        "isDeleted": "is_deleted",
        "tokenType": "token_type",
        "maxSupply": "max_supply",
        "adminKey": "admin_key",
        "kycKey": "kyc_key",
        "freezeKey": "freeze_key",
        "wipeKey": "wipe_key",
        "supplyKey": "supply_key",
        "defaultFreezeStatus": "default_freeze_status",
        "defaultKycStatus": "default_kyc_status",
        "autoRenewAccount": "auto_renew_account",
        "autoRenewPeriod": "auto_renew_period",
        "pauseKey": "pause_key",
        "pauseStatus": "pause_status",
        "supplyType": "supply_type",

        "serialNumber": "serial_number",

        "topicId": "topic_id",
        "accountId": "account_id",
        "fileId": "file_id"
    }

    def __getattr__(self, name: str) -> object:
        try:
            snake = self._ALIASES[name]
        except KeyError as exc:
            raise AttributeError(
                f"{self.__class__.__name__!r} has no attribute {name!r}"
            ) from exc

        warnings.warn(
            f"{self.__class__.__name__}.{name} will be deprecated; use .{snake}",
            FutureWarning,
            stacklevel=2,
        )
        return getattr(self, snake)

    def __setattr__(self, name: str, value: object) -> None:
        # intercept legacy writes
        if name in self._ALIASES:
            snake = self._ALIASES[name]
            warnings.warn(
                f"{self.__class__.__name__}.{name}= is deprecated; use .{snake}=",
                FutureWarning,
                stacklevel=2,
            )
            name = snake
        super().__setattr__(name, value)