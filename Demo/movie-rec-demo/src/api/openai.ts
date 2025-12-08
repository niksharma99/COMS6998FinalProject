const OPENAI_API_KEY = import.meta.env.VITE_OPENAI_API_KEY;

const SYSTEM_PROMPT = `You are a friendly movie recommendation assistant. You help users find movies they'll love based on their preferences, mood, and past favorites.

When recommending movies:
- Suggest 2-4 specific movies with year and brief explanation
- Use emoji 🎬 before each movie title
- Explain WHY each movie fits what they're looking for
- Ask follow-up questions to refine recommendations
- Be conversational and enthusiastic about film

You have knowledge of movies up to your training date. Focus on being helpful and personalized.`;

export async function getChatResponse(
  userMessage: string,
  conversationHistory: { role: 'user' | 'assistant'; content: string }[]
): Promise<string> {
  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${OPENAI_API_KEY}`,
    },
    body: JSON.stringify({
      model: 'gpt-4o-mini', // cheap and fast, swap to 'gpt-4o' if you want better
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        ...conversationHistory,
        { role: 'user', content: userMessage },
      ],
      max_tokens: 500,
      temperature: 0.7,
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to get response from OpenAI');
  }

  const data = await response.json();
  return data.choices[0].message.content;
}