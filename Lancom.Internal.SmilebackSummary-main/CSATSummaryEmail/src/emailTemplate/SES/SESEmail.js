import { SendEmailCommand } from "@aws-sdk/client-ses";
import { sesClient } from "./libs/sesClient.js";

const createSendEmailCommand = (toAddress, fromAddress, content, reportType) => {
  return new SendEmailCommand({
    Destination: {
      ToAddresses: 
        toAddress,  
    },
    Message: {
      Body: {
        Html: {
          Charset: "UTF-8",
          Data: content,
        },
        Text: {
          Charset: "UTF-8",
          Data: content,
        },
      },
      Subject: {
        Charset: "UTF-8",
        Data: "Smileback Report " + reportType,
      },
    },
    Source: fromAddress,
  });
};

const sendReport = async (sender, receiver, content, reportType) => {
  const sendEmailCommand = createSendEmailCommand(
    receiver,
    sender,
    content,
    reportType
  )
  console.log("Email Sent");

  try {
    return await sesClient.send(sendEmailCommand);
  } catch (caught) {
    if (caught instanceof Error && caught.name === "MessageRejected") {
      /** @type { import('@aws-sdk/client-ses').MessageRejected} */
      const messageRejectedError = caught;
      return messageRejectedError;
    }
    throw caught;
  }
};

export { sendReport };


