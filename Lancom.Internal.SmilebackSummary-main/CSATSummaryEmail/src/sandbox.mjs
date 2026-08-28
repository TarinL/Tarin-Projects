import { scheduledEventLoggerHandler } from "./handlers/scheduled-event-logger.js";    
import { config } from "dotenv";

config({path: './CSATSummaryEmail/.env', debug: true});
await scheduledEventLoggerHandler({}, {});


