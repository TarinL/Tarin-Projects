import { scheduledEventLoggerHandler } from "./handlers/scheduled-event-logger.js";    
import { config } from "dotenv";
import { getMonthlyReviewData } from "./smilebackApi.js";
import { loadJsonFile, saveFile, saveJsonFile, loadFile } from "./fileUtilities.js";
import { processComments } from "./dataProcessingHelpers.js";

// config({path: './CSATSummaryEmail/.env', debug: true});
// await scheduledEventLoggerHandler({}, {});

const data = await getMonthlyReviewData();
await saveJsonFile("monthlyData.json", data);
const reviews = data.results;
const sortedComments = processComments(reviews);
console.log(sortedComments.positive.length + sortedComments.neutral.length + sortedComments.negative.length);
console.log(reviews.length)
const comments = await loadFile("././comments.txt");
const tokensPerComment = (comments.length / 241) / 4;
console.log(tokensPerComment);