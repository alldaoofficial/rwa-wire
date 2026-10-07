import {createWebhookHandler} from './handler.mjs';
Deno.serve(createWebhookHandler((name: string)=>Deno.env.get(name)));
