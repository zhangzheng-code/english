import {fetchEventSource} from '@microsoft/fetch-event-source'
import type { Method } from 'axios'
export const CHAT_URL = '/ai/v1/chat'

class FatalError extends Error {}

export const sse = <T,V = any>(url:string,method:Method = "POST",body:V,callback?: (data:T) => void,errorCallback?: (error:Error) => void) => {
    const ctrl = new AbortController();
    fetchEventSource(url,{
        method:method.toLowerCase(),
        headers:{
            'Content-Type':'application/json'
        },
        body:JSON.stringify(body),
        signal: ctrl.signal,
        onmessage:(event) => {
            if (event.data) {
                try {
                    callback?.(JSON.parse(event.data) as T)
                } catch (e) {
                    console.error("SSE parse error:", e);
                }
            }
        },
        onclose: () => {
            ctrl.abort();
            throw new FatalError("Stream completed cleanly");
        },
        onerror:(error) => {
            ctrl.abort();
            if (error instanceof FatalError) {
                throw error; // 正常流结束，直接抛出终止重连
            }
            errorCallback?.(error);
            throw new FatalError("Stream errored or aborted"); // 抛出异常以阻止 fetchEventSource 无限循环重连
        },
    })
    return ctrl;
}