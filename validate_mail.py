#!/usr/bin/env python3
###############################################################################
# Library Imports
###############################################################################

import logging
import smtplib
import dns.resolver
import click
from email_validator import validate_email

###############################################################################
# Internal Utility Function Definitions
###############################################################################


def configure_logging(verbose):
    """
    Configures the logging settings based on the verbosity level.

    Args:
        verbose (bool): A boolean indicating whether to enable verbose logging.

    Returns:
        logger (logging.Logger): The configured logger object.

    """
    logger = logging.getLogger(__name__)

    if verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(levelname) -8s %(asctime)s %(funcName) -25s"
            " %(lineno) -5d: %(message)s",
        )
        logger.info("Logging level: DEBUG")
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(levelname) -8s %(asctime)s %(funcName) -25s"
            " %(lineno) -5d: %(message)s",
        )
        logger.info("Logging level: INFO")
    return logger


@click.command(help=__doc__)
@click.option("--verbose", "-v", is_flag=True, help="Print more debugging output.")
@click.option('--inputfile',
              type=str,
              required=True,
              help="Specify a text file of email addresses to process.")
@click.option('--outputfile',
              type=str,
              required=True,
              help="Specify a text file of email addresses to process.")

def main(verbose, inputfile, outputfile):
    """
    The main function of the email validation script.

    Args:
        verbose (bool): A boolean indicating whether to enable verbose logging.
        inputfile (str): The path to the input file containing email addresses to validate.
        outputfile (str): The path to the output file to write the cleaned email addresses.

    Returns:
        None

    Raises:
        ValueError: If the email address has bad syntax.

    This function reads email addresses from the input file, validates them using the email_validator library,
    performs DNS lookup to check the domain, and tests SMTP connectivity to verify the email addresses.
    The cleaned email addresses are then written to the output file.

    """
    configure_logging(verbose)

    logging.info("Starting application...")

    fromAddress = "info@debug.org"

    with open(outputfile, "w+") as CleanedEmailAddressfile:
        # Open the input file for reading
        with open(inputfile, "r") as EmailAddressfile:
            # Iterate through each line in the file
            for addressToVerify in EmailAddressfile:
                addressToVerify = addressToVerify.strip()

                ##############################
                # Use email_validator
                try:
                    emailObject = validate_email(addressToVerify)
                    logging.info(f"email_validator validated: {emailObject.email}")
                except:
                    logging.info(f"Email not validated: {addressToVerify}")

                ##############################
                # Get domain for DNS lookup
                splitAddress = addressToVerify.split("@")
                domain = str(splitAddress[1])

                ##############################
                # MX record lookup
                try:
                    records = dns.resolver.resolve(domain, "MX")
                    mxRecord = records[0].exchange
                    mxRecord = str(mxRecord)
                except:
                    logging.info(f"DNS domain not validated oon: {domain}")
                    continue

                ##############################
                # SMTP lib setup (use debug level for full output)
                server = smtplib.SMTP()
                server.set_debuglevel(logging.NOTSET)

                # SMTP Conversation
                try:
                    server.connect(mxRecord)
                    server.helo(
                        server.local_hostname
                    )  ### server.local_hostname(Get local server hostname)
                    server.mail(fromAddress)
                    code, message = server.rcpt(str(addressToVerify))
                    server.quit()

                    # Assume SMTP response 250 is success
                    if code == 250:
                        logging.info(f"SMTP test on {addressToVerify}: Success")
                    else:
                        logging.info(f"SMTP test on {addressToVerify}: Failed")
                        continue
                except:
                    logging.info(f"SMTP Server not validated: {addressToVerify}")

                # Write a clean email address to the output file
                logging.info(f"Adding {addressToVerify} to the output file.")
                CleanedEmailAddressfile.write(addressToVerify + "\n")
                CleanedEmailAddressfile.flush()

if __name__ == "__main__":
    main()
