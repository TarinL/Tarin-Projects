import {config} from "dotenv";
config();

function loadSmilebackConfig() {
    return {
        url: process.env.URL,
        clientId: process.env.CLIENT_ID,
        secret: process.env.SECRET,
        email: process.env.EMAIL,
        password: process.env.PASSWORD
    }
}
const smilebackConfig = loadSmilebackConfig();
export {smilebackConfig};
