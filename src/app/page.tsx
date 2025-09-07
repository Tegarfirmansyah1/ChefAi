"use client"; 
import { useState, useRef, useEffect, FormEvent } from 'react';
import { marked } from 'marked';

interface Message {
    sender: 'user' | 'ai';
    text: string;
}

export default function ChatPage() {
    const [messages, setMessages] = useState<Message[]>([
    { sender: 'ai', text: '<span class="text-gray-900"> Halo! Saya AI Chef, asisten resep pribadimu. Tanyakan apa saja tentang masakan Indonesia!' }
    ]);
    const [userInput, setUserInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [sessionId, setSessionId] = useState('')
    const chatContainerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
    setSessionId(`session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`);
    }, []);

    useEffect(() => {
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        const question = userInput.trim();
        if (!question || isLoading) return;

        setMessages(prev => [...prev, { sender: 'user', text: question }]);
        setUserInput('');
        setIsLoading(true);

        setMessages(prev => [...prev, { sender: 'ai', text: '' }]);

        try {
              const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question, session_id: sessionId })
            });

            if (!response.ok || !response.body) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value, { stream: true });
                
                setMessages(prev => {
                    const lastMessage = prev[prev.length - 1];
                    const updatedText = lastMessage.text + chunk;
                    return [...prev.slice(0, -1), { ...lastMessage, text: updatedText }];
                });
            }

        } catch (error) {
            console.error('Error fetching AI response:', error);
            setMessages(prev => {
                const lastMessage = prev[prev.length - 1];
                const errorText = '<span class="text-red-500">Maaf, terjadi kesalahan. Coba ajukan pertanyaan lagi.</span>';
                return [...prev.slice(0, -1), { ...lastMessage, text: errorText }];
            });
        } finally {
            setIsLoading(false);
        }
    };

    const renderHTML = (text: string) => {
        return { __html: marked.parse(text) };
    };

    return (
        <div className="bg-gray-100 flex flex-col h-screen font-sans">
            <header className="bg-white shadow-md p-4 flex items-center shrink-0">
                <div className="w-12 h-12 bg-amber-500 rounded-full flex items-center justify-center mr-4">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a2 2 0 01-2-2V4a2 2 0 012-2h8a2 2 0 012 2v4z" /></svg>
                </div>
                <div>
                    <h1 className="text-xl font-bold text-gray-800">AI Chef</h1>
                    <p className="text-sm text-green-500 font-medium">● Online</p>
                </div>
            </header>

            <main ref={chatContainerRef} className="flex-1 p-4 overflow-y-auto">
                <div className="space-y-4">
                    {messages.map((msg, index) => (
                        <div key={index} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                            <div 
                                className={`rounded-lg p-3 max-w-lg prose prose-sm ${msg.sender === 'user' ? 'bg-amber-500 text-white' : 'bg-white text-gray-900'}`}
                                dangerouslySetInnerHTML={renderHTML(msg.text)}
                            />
                        </div>
                    ))}
                    {isLoading && messages[messages.length - 1].sender === 'user' && (
                         <div className="flex justify-start">
                            <div className="bg-white rounded-lg p-3 max-w-lg">
                                <span className="italic text-gray-900">AI Chef sedang mengetik...</span>
                            </div>
                        </div>
                    )}
                </div>
            </main>

            <footer className="bg-white p-4 border-t shrink-0">
                <form onSubmit={handleSubmit} className="flex items-center space-x-4">
                    <input 
                        type="text" 
                        value={userInput}
                        onChange={(e) => setUserInput(e.target.value)}
                        placeholder="Ketik pertanyaanmu di sini..." 
                        autoComplete="off"
                        disabled={isLoading}
                        className="flex-1 p-3 text-gray-900 border rounded-full focus:outline-none focus:ring-2 focus:ring-amber-500 transition disabled:bg-gray-200"
                    />
                    <button 
                        type="submit" 
                        disabled={isLoading}
                        className="bg-amber-500 text-white rounded-full p-3 hover:bg-amber-600 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 transition disabled:bg-gray-400"
                    >
                        {isLoading ? (
                            <div className="w-6 h-6 border-t-2 border-white rounded-full animate-spin"></div>
                        ) : (
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" /></svg>
                        )}
                    </button>
                </form>
            </footer>
        </div>
    );
}
