// Simple keyword-based mock responses
// TODO: Replace with actual AgenticFlow API integration

const responses: { keywords: string[]; response: string }[] = [
  {
    keywords: ['sci-fi', 'science fiction', 'space', 'future'],
    response: `Great choice! For sci-fi, I'd recommend:

🎬 **Interstellar** (2014) - Epic space exploration with stunning visuals and emotional depth. If you loved Inception, this is a must-watch.

🎬 **Ex Machina** (2015) - A thought-provoking take on AI and consciousness. Intimate and unsettling.

🎬 **Arrival** (2016) - A beautiful, cerebral first contact story. More about language and time than action.

Would you like more details on any of these?`,
  },
  {
    keywords: ['funny', 'comedy', 'laugh', 'hilarious'],
    response: `Looking for laughs? Here are some great picks:

🎬 **The Grand Budapest Hotel** (2014) - Wes Anderson's quirky masterpiece with witty dialogue throughout.

🎬 **Superbad** (2007) - Classic coming-of-age comedy that still holds up.

🎬 **Game Night** (2018) - Surprisingly clever action-comedy with great ensemble chemistry.

What kind of comedy vibe are you feeling - witty, slapstick, or dark humor?`,
  },
  {
    keywords: ['scary', 'horror', 'thriller', 'suspense', 'creepy'],
    response: `For something thrilling, check out:

🎬 **Get Out** (2017) - Smart social horror that keeps you on edge. A modern classic.

🎬 **Hereditary** (2018) - Deeply unsettling family drama turned nightmare. Not for the faint of heart.

🎬 **Se7en** (1995) - Dark detective thriller with an unforgettable ending.

Do you prefer psychological horror or more supernatural scares?`,
  },
  {
    keywords: ['sad', 'emotional', 'cry', 'drama', 'feel'],
    response: `For an emotional journey:

🎬 **Good Will Hunting** (1997) - Beautiful story about potential, trauma, and human connection. You'll feel everything.

🎬 **The Shawshank Redemption** (1994) - Hope and friendship in the darkest place. A masterpiece.

🎬 **Eternal Sunshine of the Spotless Mind** (2004) - Bittersweet exploration of love and memory.

Fair warning - keep tissues nearby! 🥲`,
  },
  {
    keywords: ['action', 'exciting', 'adrenaline', 'intense'],
    response: `For an adrenaline rush:

🎬 **Mad Max: Fury Road** (2015) - Two hours of non-stop, beautifully choreographed chaos.

🎬 **John Wick** (2014) - Sleek, stylish action with incredible fight choreography.

🎬 **The Dark Knight** (2008) - Superhero action elevated to crime epic status.

Want something more recent, or are classics okay?`,
  },
  {
    keywords: ['team', 'ensemble', 'group', 'friends', 'crew'],
    response: `Love great team dynamics? Try these:

🎬 **Ocean's Eleven** (2001) - The ultimate heist crew with incredible chemistry and witty banter.

🎬 **Guardians of the Galaxy** (2014) - Ragtag misfits becoming family, with a killer soundtrack.

🎬 **The Departed** (2006) - Tense ensemble thriller with an incredible cast playing off each other.

These all have that "found family" energy where the team interactions are the highlight!`,
  },
  {
    keywords: ['recommend', 'suggestion', 'watch', 'movie', 'tonight'],
    response: `I'd love to help! To give you the perfect recommendation, tell me:

- What mood are you in? (fun, thoughtful, thrilling, emotional)
- Any genres you're feeling? (sci-fi, comedy, drama, action)
- Recent movie you loved? (I can find similar ones)

Or just describe what you're looking for in your own words!`,
  },
  {
    keywords: ['inception', 'nolan', 'christopher'],
    response: `Ah, a Nolan fan! Based on Inception, you might love:

🎬 **The Prestige** (2006) - Another Nolan mind-bender about obsession and sacrifice. The twist is *chef's kiss*.

🎬 **Memento** (2000) - Where it all started. Reverse chronology that rewards rewatching.

🎬 **Tenet** (2020) - Time inversion espionage. Even more puzzle-box than Inception.

All of these share that "I need to watch it again to catch everything" quality!`,
  },
];

const defaultResponse = `That's interesting! I'm still learning about different movie preferences.

Could you tell me more about what you're looking for? For example:
- A specific genre (action, comedy, drama, sci-fi)
- A mood (something light, intense, thought-provoking)
- A movie you loved that you want more of

I'm here to help find your next favorite film! 🎬`;

export function getMockResponse(input: string): string {
  const lowerInput = input.toLowerCase();
  
  for (const { keywords, response } of responses) {
    if (keywords.some(keyword => lowerInput.includes(keyword))) {
      return response;
    }
  }
  
  return defaultResponse;
}