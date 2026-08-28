import {getWeeklyReviewData, getMonthlyReviewData} from "../smilebackApi.js";
import {loadFile, saveFile} from "../fileUtilities.js";
import {createMonthlyEmail, createWeeklyEmail} from "../emailTemplate/emailHelperFunctions.js";
import { sendReport } from "../emailTemplate/SES/SESEmail.js";
import { assertValidData } from "../dataProcessingHelpers.js";

export const scheduledEventLoggerHandler = async (event, context) => {
    const date = new Date(new Date().toLocaleString("en-US", {timeZone: "Pacific/Auckland"})); // timezone
    const sender = process.env.SENDER;
    let receivers = process.env.RECEIVER;
    receivers = receivers.split(",");
    if (date.getDate() === 1) { // checks if it is the first day of the month
        const monthlyData = await getMonthlyReviewData();
        if (assertValidData(monthlyData)) {
            const monthlyReviews = monthlyData['results'];
            let monthlyTemplate = await loadFile("./src/emailTemplate/monthlyTemplate.html");
            monthlyTemplate = createMonthlyEmail(monthlyTemplate, monthlyReviews);
            await sendReport(sender, receivers, monthlyTemplate, "Monthly");
    }
    }
    if (date.getDay() === 1) { // checks if it is Monday
        const weeklyData= await getWeeklyReviewData();
        if (assertValidData(weeklyData)) {
            const weeklyReviews = weeklyData['results'];
            let weeklyTemplate = await loadFile("./src/emailTemplate/weeklyTemplate.html");
            weeklyTemplate = createWeeklyEmail(weeklyTemplate, weeklyReviews);
            await sendReport(sender, receivers, weeklyTemplate, "Weekly");  
        }     
    } 
}
