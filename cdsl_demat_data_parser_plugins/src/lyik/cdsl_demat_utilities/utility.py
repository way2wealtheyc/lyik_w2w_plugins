from lyikpluginmanager.models.cdsl.helper_enums import *
from lyikpluginmanager.models.cdsl.state_codes import StateCode
from lyikpluginmanager.models import Signature
from typing import List
from .models.models import NominationDetails, NomineeData, GuardianData, Nominee


class HolderType(str, Enum):
    KYC_HOLDER = "KYC Holder"
    NOMINEE = "Nominee"
    NOMINEE_GUARDIAN = "Nominee Guardian"


class AddressType(str, Enum):
    COR = "Corresepondence Address"
    PERM = "Permanent Address"


class CDSLDematUtility:
    def __init__(self, form_record: dict):
        """
        # Todo:
        -   Add form_identifier logic based on form_record data.
            This will decide how to get values of record json!

        """
        self.form_record = form_record
        # todo: kyc data based on form-identifier!
        self.kyc_data = [
            kyc_holder.get("kyc_holder", {})
            for kyc_holder in form_record.get("kyc_holders", [])
        ]
        self.nomination_details = NominationDetails(
            form_record.get("nomination_details", {})
        )

    def product_number_value(self):
        # Product Number / Client Type
        return ProductNumber.IND  # condidering client type of Individual only!

    def beneficiary_subtype_value(self):
        # Todo: why not just Individual(INDVL)?
        return BeneficiarySubType.INRES  # Individual-Resident / Ordinary

    def purpose_value(self, holder_type: HolderType, index: int):
        # Todo: this method only handles holder(FH,SH,TH), nominee(NM) and Nominee-Guardian(NMG) types, not even guardian(GD) and other types!
        if holder_type == HolderType.KYC_HOLDER:
            if index == 0:
                return Purpose.FH
            if index == 1:
                return Purpose.SH
            if index == 2:
                return Purpose.TH

        if holder_type == HolderType.NOMINEE:
            return Purpose.NM

        if holder_type == HolderType.NOMINEE_GUARDIAN:
            return Purpose.NMG

        return Purpose.DFT

    def first_name_value(self, index):
        # Todo: Putting (full) name as per PAN, as fname, mnane, lname fields are not present in form!
        fullname = (
            self.kyc_data[index]
            .get("pan_verification", {})
            .get("pan_details", {})
            .get("name_in_pan", "")
        )
        return fullname

    def father_or_husband_name_value(self, index):
        # Todo: Need clarity for this field, field name and description are seemd to be differnt!
        name = (
            self.kyc_data[index]
            .get("pan_verification", {})
            .get("pan_details", {})
            .get("parent_guardian_spouse_name", "")
        )
        return name  # currently returning spouse/father name

    def dob_value(self, index):
        """
        Gives DoB as in PAN
        """
        pan_dob = (
            self.kyc_data[index]
            .get("pan_verification", {})
            .get("pan_details", {})
            .get("dob_pan", "")
        )
        return self.format_date(date=pan_dob)

    def gender_value(self, index):
        gender = (
            self.kyc_data[index]
            .get("identity_address_verification", {})
            .get("identity_address_info", {})
            .get("gender", "")
        )
        if not gender:
            return None
        if gender == "M":
            return Gender.MALE
        if gender == "F":
            return Gender.FMALE
        if gender == "T":
            return Gender.TRGEN

        return Gender.DFT

    def pan_num_value(self, index):
        pan = (
            self.kyc_data[index]
            .get("pan_verification", {})
            .get("pan_details", {})
            .get("pan_number", "")
        )
        return pan

    def pan_verification_flag(self, index):
        # Mandatory only when PAN is present
        pan = self.pan_num_value(index=index)
        if not pan:
            return None
        pan_seed_status = (
            self.form_record.get("dp_information", {})
            .get("standing_info_from_client", {})
            .get("aadhaar_pan_seed_status", "")
        )
        if pan_seed_status == "YES":
            return (
                PANVerificationFlag.PANVAL
            )  # # PAN Verified and Aadhar Linked / PAN verified and seeded with Adhaar (Updated By Depository)
        if pan_seed_status == "NO":
            return PANVerificationFlag.PANVNS  # PAN Verified,Aadhar link to be checked
        if pan_seed_status == "EXEMPTED":
            return PANVerificationFlag.AEXMPT
        return PANVerificationFlag.DFT

    # def aadhaar_uid_value(self, index):
    #     return ''

    def aadhaar_authenticated_value(self, index):
        # Aadhaar Authenticated with UIDAI/ UID VERIFICATION FLAG
        # Todo: if digilocker aadhaar, return 'ADRV', else 'ADRNV'
        is_digilocker = (
            str(
                self.form_record.get("application_details", {}).get(
                    "kyc_digilocker", ""
                )
            ).lower()
            != "no"
        )
        aadhaar_uid = (
            self.kyc_data[index]
            .get("identity_address_verification", {})
            .get("identity_address_info", {})
            .get("uid", "")
        )
        if is_digilocker and aadhaar_uid:
            return AadhaarAuthenticationWithUIDFlag.ADRV

        return None

    def sms_facility_value(self):
        # Todo: value in 2 places: under TnC section and also in dp_information!
        sms_selection = (
            self.form_record.get("dp_information", {})
            .get("standing_info_from_client", {})
            .get("first_holder_sms_alert", "")
        )
        if not sms_selection:
            return SMSFacility.DFT
        if (
            sms_selection == "NO"
        ):  # Todo: need to check whether it's 'NO' or something else
            return SMSFacility.NO

        return SMSFacility.YES

    def primary_isd_code_value(self, index: int):
        # Currenly setting '91' hard coded!
        return "91"

    def mobile_num_value(self, index):
        mobile = (
            self.kyc_data[index]
            .get("mobile_email_verification", {})
            .get("mobile_verification", {})
            .get("contact_id", "")
        )
        return mobile

    def email_value(self, index):
        email = (
            self.kyc_data[index]
            .get("mobile_email_verification", {})
            .get("email_verification", {})
            .get("contact_id", "")
        )
        return email

    def family_flag_email_value(self, index):
        # Todo: unknown source of data
        return FamilyFlagForEmail.DFT

    def mode_of_operation_value(self):
        # Mode of Operation:
        # # todo: need clarity on what the field is?
        #           whether it is sole holder vs 1+ holder
        #           or some other field value like field having first holder, all joint holder options!
        #           as one option include any one(ANOSUR) too

        if len(self.kyc_data) == 1:
            return ModeOfOperation.SLHLD
        return ModeOfOperation.JTHLDR  # why not ANOSUR(any one or survivor)?

    def standing_instruction_indicator_value(self):
        # unkown source of data
        return StandingInstructionIndicator.DFT

    def gross_income_value(self, index):
        income = (
            self.kyc_data[index]
            .get("declarations", {})
            .get("income_info", {})
            .get("gross_annual_income", "")
        )
        if income == "UPTO_1L":
            return GrossAnnualIncomeRange.UPT1L.value
        if income == "1_TO_5L":
            return GrossAnnualIncomeRange._1LT5L.value
        if income == "5_TO_10L":
            return GrossAnnualIncomeRange._5LTXL.value
        if income == "10_TO_25L":
            return GrossAnnualIncomeRange.XLTXXV.value
        if income == "25L_TO_1CR":
            return GrossAnnualIncomeRange._25T1CR.value
        if income == "1CR_TO_5CR":
            return GrossAnnualIncomeRange.GT1CR.value
        return GrossAnnualIncomeRange.DFT.value

    def bank_ifsc_value(self):
        bank_ifsc = (
            self.form_record.get("bank_verification", {})
            .get("bank_details", {})
            .get("ifsc_code", "")
        )
        return bank_ifsc

    def bank_micrcd_value(self):
        bank_micrid = (
            self.form_record.get("bank_verification", {})
            .get("bank_details", {})
            .get("micr_code", "")
        )
        return bank_micrid

    def ecs_mandate_value(self):
        # Todo: unknown field source
        return ECSMandate.DFT  # Todo: need to be changed as we get more info

    def education_level_value(self):
        # Todo: unknown field source
        return EducationDegree.DFT

    def annual_report_flag(self):
        receive_annual_report = (
            self.form_record.get("dp_information", {})
            .get("standing_info_from_client", {})
            .get("receive_annual_report", "")
        )
        if receive_annual_report == "ELECTRONIC":
            return AnnualReportFlag.ELC
        if receive_annual_report == "PHYSICAL":
            return AnnualReportFlag.PHY
        return AnnualReportFlag.DFT

    def bo_statement_cycle_code_value(self):
        acc_statement_requirement = (
            self.form_record.get("dp_information", {})
            .get("standing_info_from_client", {})
            .get("account_statement_requirement", "")
        )
        if acc_statement_requirement == "WEEKLY":
            return BOStatementCycleCode.EW
        if acc_statement_requirement == "MONTHLY":
            return BOStatementCycleCode.EM

        return BOStatementCycleCode.DF

    def electronic_confiramtion_value(self):
        eth = (
            self.form_record.get("dp_information", {})
            .get("standing_info_from_client", {})
            .get("electronic_transaction_holding_statement", "")
        )
        if eth == "YES":
            return ElectronicConfitmation.YES
        if eth == "NO":
            return ElectronicConfitmation.NO
        return ElectronicConfitmation.DFT

    def email_rta_download_value(self):
        rta = (
            self.form_record.get("dp_information", {})
            .get("standing_info_from_client", {})
            .get("share_email_id_with_rta", "")
        )
        if rta == "YES":
            return EmailRTADDwonloadFlag.YES
        if rta == "NO":
            return EmailRTADDwonloadFlag.NO
        return EmailRTADDwonloadFlag.DFT

    def pledge_instruction_value(self):
        rta = (
            self.form_record.get("dp_information", {})
            .get("standing_info_from_client", {})
            .get("auto_pledge_confirmation", "")
        )
        if rta == "YES":
            return AutoPledgeIndicator.YES
        if rta == "NO":
            return AutoPledgeIndicator.NO
        return AutoPledgeIndicator.DFT

    def exchange_value(self):
        # Todo: Does CDSL repository means exchange to be filled as BSE, and NSE for NSDL?
        depository = (
            self.form_record.get("dp_information", {})
            .get("dp_Account_information", {})
            .get("depository", "")
        )
        if depository == "NSDL":
            return Exchange.NSE
        if depository == "CDSL":
            return Exchange.BSE
        return Exchange.DFT

    def nationality_value(self):
        # Todo: Nationality field missing in form

        return Nationality.IN

    def bank_account_type_value(self):
        # Todo: account type field missing in form
        return BankAccountType.DFT

    def bo_category_value(self):
        return BOCategory.NHB  # Todo: Need a deciding factor

    def bank_acc_no_value(self):
        acc_num = (
            self.form_record.get("bank_verification", {})
            .get("bank_details", {})
            .get("bank_account_number", "")
        )
        return acc_num

    def tax_deduction_status_value(self):
        # Currently considering just RI type of clients!
        return BeneficiaryTaxDeductionStatus.RI

    def bsda_flag_value(self):
        bsda_flag = (
            self.form_record.get("dp_information", {})
            .get("standing_info_from_client", {})
            .get("bsda", "")
        )
        if bsda_flag == "YES":
            return BSDAFlag.BSDA
        if bsda_flag == "NO":
            return BSDAFlag.NBSD
        return BSDAFlag.DFT

    def occupation_value(self, index):
        occupation = (
            self.kyc_data[index]
            .get("declarations", {})
            .get("income_info", {})
            .get("occupation", "")
        )
        if occupation == "PUBLIC_SECTOR":
            return Occupation.PUS
        if occupation == "PRIVATE_SECTOR":
            return Occupation.PRS
        if occupation == "GOVT_SERVICE":
            return Occupation.GOV
        if occupation == "BUSINESS":
            return Occupation.BUS
        if occupation == "PROFESSIONAL":
            return Occupation.PRO
        if occupation == "AGRICULTURIST":
            return Occupation.FAR
        if occupation == "RETIRED":
            return Occupation.RET
        if occupation == "HOUSE_WIFE":
            return Occupation.HOU
        if occupation == "STUDENT":
            return Occupation.STU
        if occupation == "OTHERS":
            return Occupation.OTH
        return Occupation.DFT

    def communication_pref_value(self):
        com_pref = (
            self.form_record.get("dp_information", {})
            .get("standing_info_from_client", {})
            .get("first_holder_sms_alert", "")
        )
        if com_pref == "FIRST_HOLDER":
            return CommunicationPreference.FIH
        if com_pref == "ALL_HOLDERS":
            return CommunicationPreference.ALH
        return CommunicationPreference.DFT

    def account_opening_source_value(self):
        return AccountOpeningSource.OLAO  # Todo: Unknown source of data

    def first_client_option_to_recieve_statement_value(self):
        recieve_statement = (
            self.form_record.get("dp_information", {})
            .get("standing_info_from_client", {})
            .get("electronic_transaction_holding_statement", "")
        )
        if recieve_statement == "YES":
            return EmailStatementFlag.ELE
        if recieve_statement == "NO":
            return EmailStatementFlag.PHY
        return EmailStatementFlag.DFT

    def sender_reference_number_value(self, index):
        # Unknown source of data
        return f"AOI781{index}"

    def holder_purpose_code_value(self, address_type: AddressType):
        if address_type == AddressType.COR:
            return PurposeCode.CORAD
        if address_type == AddressType.PERM:
            return PurposeCode.PERAD
        return PurposeCode.DFT

    def holder_address_value(self, index, address_type: PurposeCode):
        if address_type == PurposeCode.CORAD:
            return (
                self.kyc_data[index]
                .get("identity_address_verification", {})
                .get("correspondence_address", {})
                .get("full_address", "")
            )
        return (
            self.kyc_data[index]
            .get("identity_address_verification", {})
            .get("identity_address_info", {})
            .get("full_address", "")
        )

    def is_permanent_address(self, index):
        return (
            True
            if self.kyc_data[index]
            .get("identity_address_verification", {})
            .get("identity_address_info", {})
            .get("full_address", "")
            else False
        )

    def is_corr_address(self, index):
        return (
            True
            if self.kyc_data[index]
            .get("identity_address_verification", {})
            .get("correspondence_address", {})
            .get("full_address", "")
            else False
        )

    def holder_country_value(self, index, address_type: PurposeCode):
        if address_type == PurposeCode.CORAD:
            country = (
                self.kyc_data[index]
                .get("identity_address_verification", {})
                .get("correspondence_address", {})
                .get("country", "")
            )
        elif address_type == PurposeCode.PERAD:
            country = (
                self.kyc_data[index]
                .get("identity_address_verification", {})
                .get("identity_address_info", {})
                .get("country", "")
            )
        else:
            return None
        return self._country_value(country=str(country).lower())

    def holder_address_pincode(self, index, address_type: PurposeCode):
        if address_type == PurposeCode.CORAD:
            return (
                self.kyc_data[index]
                .get("identity_address_verification", {})
                .get("correspondence_address", {})
                .get("pin", "")
            )
        if address_type == PurposeCode.PERAD:
            return (
                self.kyc_data[index]
                .get("identity_address_verification", {})
                .get("identity_address_info", {})
                .get("pin", "")
            )
        return None

    def holder_state_code(self, index, address_type: PurposeCode):
        if address_type == PurposeCode.CORAD:
            state = (
                self.kyc_data[index]
                .get("identity_address_verification", {})
                .get("correspondence_address", {})
                .get("country", "")
            )
        elif address_type == PurposeCode.PERAD:
            state = (
                self.kyc_data[index]
                .get("identity_address_verification", {})
                .get("identity_address_info", {})
                .get("country", "")
            )
        else:
            return None
        return StateCode.get(state, "DFT")

    def _country_value(self, country: str):

        country_code = (
            AddressCountryCode.IN if country == "india" else AddressCountryCode.DFT
        )
        return country_code

    def format_date(self, date: str) -> str:
        """
        returns date in YYYY-MM-DD format
        """
        from datetime import datetime

        if not date:
            return None
        try:
            # Parse the input string into a datetime object
            # dt = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')
            dt = datetime.strptime(date, "%d/%m/%Y")
            # Format the datetime object into the desired format
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            # logger.debug(f"Error in formatting date {date}")
            return None

    def get_all_signature_ids(self) -> List[Signature]:
        signs: List[Signature] = []

        try:
            # Add Holders Signs
            for i in range(len(self.kyc_data)):
                doc_id = (
                    self.kyc_data[i]
                    .get("signature_validation", {})
                    .get("upload_images", {})
                    .get("wet_signature_image", {})
                    .get("doc_id")
                )
                if doc_id:
                    file_name = (
                        self.kyc_data[i]
                        .get("signature_validation", {})
                        .get("upload_images", {})
                        .get("wet_signature_image", "")
                        .get("doc_name")
                    )
                    signs.append(Signature(file_name=file_name, doc_id=doc_id))

        # Add other signs?

        except Exception as e:
            return []

        return signs

    def nominees(self):
        return self.nomination_details.nominees

    def nominee_purpose_code(self):
        return PurposeCode.NOMAD

    def nominee_guardian_purpose_code(self):
        return PurposeCode.MNGAD

    def nominee_minor_indicator(self) -> NomineeMinorIndicator:
        minors = [
            nominee.nominee_data.is_minor
            for nominee in self.nomination_details.nominees
        ]

        num_nominees = len(minors)
        if num_nominees == 0:
            return NomineeMinorIndicator.DFT

        # Pad with False if less than 3 nominees
        while len(minors) < 3:
            minors.append(False)

        if num_nominees > 0 and all(minors[:num_nominees]):
            return NomineeMinorIndicator.ANM
        elif num_nominees >= 2 and minors[0] and minors[1] and not minors[2]:
            return NomineeMinorIndicator.FSM
        elif num_nominees >= 3 and minors[0] and not minors[1] and minors[2]:
            return NomineeMinorIndicator.FTM
        elif num_nominees >= 3 and not minors[0] and minors[1] and minors[2]:
            return NomineeMinorIndicator.STM
        elif minors[0]:
            return NomineeMinorIndicator.FNM
        elif num_nominees >= 2 and minors[1]:
            return NomineeMinorIndicator.SNM
        elif num_nominees >= 3 and minors[2]:
            return NomineeMinorIndicator.TNM
        else:
            return NomineeMinorIndicator.DFT

    def nominee_first_name(self, nominee: NomineeData) -> str:
        return nominee.name_of_nominee

    def nominee_guardian_name(self, guardian_data: GuardianData) -> str:
        return guardian_data.guardian_name

    def nominee_dob(self, nominee: NomineeData):
        return self.format_date(date=nominee.dob_nominee)

    def nominee_equal_share_flag(self) -> FlagForSharePercentageEquality:
        nominees = self.nominees()
        shares = [n.nominee_data.percentage_of_allocation for n in nominees]

        # If there are no nominees or only one nominee, return DFT
        if len(shares) <= 1:
            return FlagForSharePercentageEquality.DFT

        # Check if all shares are equal by comparing each with the first one
        if all(share == shares[0] for share in shares):
            return FlagForSharePercentageEquality.YES
        else:
            return FlagForSharePercentageEquality.NO

    # In nm_or_grdn_add_prsnt method:
    def nm_or_grdn_add_prsnt(self, nominee: Nominee) -> NomineeGuardianAddressPresent:
        return (
            NomineeGuardianAddressPresent.YES
            if (
                nominee.nominee_data.nominee_address
                or nominee.guardian_data.guardian_address
            )
            else NomineeGuardianAddressPresent.NO
        )

    def nmnor_grdn_add_prsnt(
        self, guardian_data: GuardianData
    ) -> MinorNomineeGuardianAddressPresent:
        if guardian_data.guardian_address:
            return MinorNomineeGuardianAddressPresent.YES
        else:
            return MinorNomineeGuardianAddressPresent.NO
