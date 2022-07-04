# -*- coding: utf-8 -*-
"""
Created June 2022
Niklas Österlund
"""
import os
from azure.storage.blob.appendblobservice import AppendBlobService


class AzureLogger(object):
    def __init__(self, container_name="qr-attendance", blob_name="attendance.log"):
        self.container_name = container_name
        self.connect()

    def connect(self, connection_string=None, account_name=None, sas_token=None):
        """
        Before being able to log, you must connect to the storage account.

        Make sure the environment variables below are set

        Parameters
        ----------
        connection_string : TYPE, optional
            The connection string, if this is used, account name and sas token is not needed.
        account_name : TYPE, optional
            If no connection string, you need both account name and sas token.
        sas_token : TYPE, optional
            If no connection string, you need both account name and sas token.
        """
        connection_string = None
        account_name = None
        sas_token = None
        try:
            connection_string = os.environ["QR_LOGGER_CONNECTION_STRING"]
        except Exception:
            account_name = os.environ["QR_LOGGER_ACCOUNT_NAME"]
            sas_token = os.environ["QR_LOGGER_SAS_TOKEN"]
        self.service = AppendBlobService(
            connection_string=connection_string,
            account_name=account_name,
            sas_token=sas_token,
        )
        blobs = self.service.list_blobs(self.container_name)
        self.existing_log_files = []
        for blob in blobs:
            self.existing_log_files.append(blob.name)

    def log(self, text, blob_name="attendance.log"):
        """
        You must have connected before you can start to log text.

        Parameters
        ----------
        text : str
            the text you want to append to the log. Note that you need to add a newline
            to the string if you want to add that
        blob_name : str, optional
            The output file name. The default is "attendance.log".

        Raises
        ------
        NameError
            DESCRIPTION.

        Returns
        -------
        None.

        """
        if self.service is None:
            raise NameError("You are not connected")
        if blob_name not in self.existing_log_files:
            self.service.create_blob(
                container_name=self.container_name, blob_name=blob_name
            )
            self.existing_log_files.append(blob_name)
        self.service.append_blob_from_text(
            container_name=self.container_name,
            blob_name=blob_name,
            text=text,
            timeout=5,
        )
        return True
