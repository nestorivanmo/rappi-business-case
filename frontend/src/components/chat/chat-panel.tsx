"use client";

import { useState } from "react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { MessageList } from "./message-list";
import { MessageInput } from "./message-input";
import { useChat } from "@/hooks/use-chat";

export function ChatPanel({ kam }: { kam: string }) {
  const [open, setOpen] = useState(false);
  const { messages, sendMessage, isStreaming, clearMessages } = useChat(kam);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger
        className="fixed bottom-6 right-6 h-12 w-12 rounded-full shadow-lg bg-orange-500 hover:bg-orange-600 text-white flex items-center justify-center cursor-pointer"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
      </SheetTrigger>
      <SheetContent className="w-[400px] sm:w-[540px] flex flex-col p-0">
        <SheetHeader className="px-4 py-3 border-b">
          <div className="flex items-center justify-between">
            <SheetTitle className="text-sm">KAM Agent - {kam}</SheetTitle>
            {messages.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearMessages}
                className="text-xs"
              >
                Clear
              </Button>
            )}
          </div>
        </SheetHeader>
        <div className="flex-1 flex flex-col overflow-hidden">
          <MessageList messages={messages} />
          <MessageInput onSend={sendMessage} disabled={isStreaming} />
        </div>
      </SheetContent>
    </Sheet>
  );
}
