import AsyncStorage from '@react-native-async-storage/async-storage';

// Key pattern: "voiceNote:{inspectionSessionId}:{itemId}"
// inspectionSessionId scopes clips to a single inspection job
// so they can be bulk-retrieved at the Confirm screen
const buildKey = (sessionId: string, itemId: string): string =>
    `voiceNote:${sessionId}:${itemId}`;

// Store a voice note URI for a specific inspection item.
// Called by the AI parser after it produces the MP4 file.
export async function storeVoiceNoteUri(
    sessionId: string,
    itemId: string,
    uri: string
): Promise<void> {
    // Guard: only store the URI string (not the file contents).
    // URIs are typically <200 chars — safe for AsyncStorage.
    // File contents must never be written to AsyncStorage directly.
    // The 1.5MB AsyncStorage limit applies to the full CompletedInspection payload,
    // not to URI strings. URI strings are negligible in size.
    if (uri.length > 500) {
        console.warn('[VoiceNoteStorage] URI unexpectedly long — verify parser output:', uri);
    }

    // PLACEHOLDER: uri is produced by AI parser — do not validate format here
    // TODO: add SHA-256 checksum verification when compilation layer is wired
    try {
        await AsyncStorage.setItem(buildKey(sessionId, itemId), uri);
    } catch (e) {
        // TODO: surface storage error to UI via error boundary or toast
        console.error('[VoiceNoteStorage] Failed to store URI:', e);
    }
}

// Retrieve a single voice note URI for a specific item.
// Returns null if no voice note has been stored for this item.
export async function getVoiceNoteUri(
    sessionId: string,
    itemId: string
): Promise<string | null> {
    try {
        return await AsyncStorage.getItem(buildKey(sessionId, itemId));
    } catch (e) {
        console.error('[VoiceNoteStorage] Failed to retrieve URI:', e);
        return null;
    }
}

// Retrieve ALL voice note URIs for an entire inspection session.
// Called at the Confirm screen to assemble the VoiceNoteCompilationPayload.
// Returns an array of { itemId, uri } pairs — omits items with no voice note.
export async function getAllVoiceNoteUrisForSession(
    sessionId: string
): Promise<{ itemId: string; uri: string }[]> {
    try {
        const allKeys = await AsyncStorage.getAllKeys();
        const sessionPrefix = `voiceNote:${sessionId}:`;
        const sessionKeys = allKeys.filter(k => k.startsWith(sessionPrefix));

        if (sessionKeys.length === 0) return [];

        const pairs = await AsyncStorage.multiGet(sessionKeys);
        return pairs
            .filter((pair): pair is [string, string] => pair[1] !== null)
            .map(([key, uri]) => ({
                itemId: key.replace(sessionPrefix, ''),
                uri,
            }));
    } catch (e) {
        console.error('[VoiceNoteStorage] Failed to retrieve session URIs:', e);
        return [];
    }
}

// Clear all voice note URIs for a session after successful submission.
// TODO: call this after the global AI overview compilation POST succeeds.
export async function clearVoiceNotesForSession(sessionId: string): Promise<void> {
    try {
        const allKeys = await AsyncStorage.getAllKeys();
        const sessionKeys = allKeys.filter(k =>
            k.startsWith(`voiceNote:${sessionId}:`)
        );
        if (sessionKeys.length > 0) {
            await AsyncStorage.multiRemove(sessionKeys);
        }
    } catch (e) {
        console.error('[VoiceNoteStorage] Failed to clear session URIs:', e);
    }
}
