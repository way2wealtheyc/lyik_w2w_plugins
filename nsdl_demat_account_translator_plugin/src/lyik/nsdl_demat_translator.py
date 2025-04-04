import apluggy as pluggy
from lyikpluginmanager import (
    getProjectName,
    ContextModel,
    NSDLDematSpec,
    NSDLRquestModel,
    GenericFormRecordModel,
    PluginException,
)
from .nsdl_demat_model.form_record_mpdel import FormRecordModel
from .form_record_mapping import map_form_record
from typing import Annotated
from typing_extensions import Doc
from lyikpluginmanager.annotation import RequiredEnv
import logging

logger = logging.getLogger(__name__)
from pydantic import ValidationError
from .nsdl_transator_utility.validation_utility import get_readable_validation_error

impl = pluggy.HookimplMarker(getProjectName())


class NSDLDemat(NSDLDematSpec):
    """"""

    @impl
    async def translate_to_nsdl_demat(
        self,
        context: ContextModel,
        form_record: Annotated[GenericFormRecordModel, Doc("Form Record")],
    ) -> Annotated[
        NSDLRquestModel,
        RequiredEnv(["NSDL_REQUESTOR_ID"]),
        Doc("The Desired output for NSDL Demat"),
    ]:
        """
        This function is to translate form record into NSDL demat request model
        """
        try:
            # Validating the form record

            form_record_model = FormRecordModel.model_validate(form_record.model_dump())
            logger.debug("Form record model parsed and validated")
            # Map the form record to NSDL demat request model
            nsdl_model = await map_form_record(
                form_record_model=form_record_model, context=context
            )

            return nsdl_model

        except ValidationError as e:
            error_details = e.errors()
            parsed_errors = f"These following data is required for NSDL Demat account creation: {get_readable_validation_error(e)}"
            raise PluginException(parsed_errors)
