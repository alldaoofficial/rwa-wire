import {createUnsubscribeHandler} from './handler.mjs';
Deno.serve(createUnsubscribeHandler((name: string)=>Deno.env.get(name)));
