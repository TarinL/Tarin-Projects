import { Amplify } from "aws-amplify";

Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: "ap-southeast-2_9OMhJP0FG",
      userPoolClientId: "2rdo1hk080nq8pdame6jv3v0jp",
    },
  },
});
