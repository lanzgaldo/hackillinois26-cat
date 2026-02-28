import React, { createContext, useContext, useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { CATEGORIES, Status } from '../constants/inspectionCategories';

export interface InspectionNote {
    id: string;
    itemId: string; // The specific checklist item ID, or 'general'
    text: string;
    type: 'voice' | 'text';
    timestamp: string;
}

export interface InspectionPhoto {
    id: string;
    itemId: string;
    uri: string;
    timestamp: string;
}

export interface InspectionItemState {
    status: Status;
    timelineEstimate?: string; // For yellow warnings
    voiceNoteUri?: string | null;
    voiceNoteTranscript?: string | null;
    voiceNoteEditedTranscript?: string | null;
    photos?: string[];
}

export interface AIReview {
    narrative: string;
    urgentFlags: string[];
    recommendedAction: string;
}

export interface InspectionState {
    assetId: string;
    elapsedSeconds: number;
    isDraft: boolean;
    isSubmitted: boolean;
    itemStates: Record<string, InspectionItemState>;
    notes: Record<string, InspectionNote[]>; // legacy
    photos: Record<string, InspectionPhoto[]>; // legacy
    aiReview: AIReview | null;
    aiReviewLoading: boolean;
    aiReviewError: boolean;
}

interface InspectionContextType {
    state: InspectionState;
    updateItemStatus: (itemId: string, status: Status, timelineEstimate?: string) => void;
    addNote: (itemId: string, text: string, type: 'voice' | 'text') => void;
    addPhoto: (itemId: string, uri: string) => void;
    submitInspection: () => void;
    resetInspection: (assetId: string) => void;
    removePhoto: (itemId: string, photoId: string) => void;
    // New Actions
    updateItemVoiceNote: (itemId: string, uri: string | null, transcript: string | null, editedTranscript?: string | null) => void;
    addItemPhoto: (itemId: string, uri: string) => void;
    removeItemPhoto: (itemId: string, uri: string) => void;
    fetchAiReview: () => Promise<void>;
}

const initialState: InspectionState = {
    assetId: '',
    elapsedSeconds: 0,
    isDraft: false,
    isSubmitted: false,
    itemStates: {},
    notes: {},
    photos: {},
    aiReview: null,
    aiReviewLoading: false,
    aiReviewError: false,
};

const InspectionContext = createContext<InspectionContextType | undefined>(undefined);

export function InspectionProvider({ children }: { children: React.ReactNode }) {
    const [state, setState] = useState<InspectionState>(initialState);
    const [isLoaded, setIsLoaded] = useState(false);

    // Load from AsyncStorage on mount
    useEffect(() => {
        const loadState = async () => {
            try {
                const saved = await AsyncStorage.getItem('@cat_inspection_state');
                if (saved) {
                    setState(JSON.parse(saved));
                }
            } catch (e) {
                console.error('Failed to load state', e);
            } finally {
                setIsLoaded(true);
            }
        };
        loadState();
    }, []);

    // Save to AsyncStorage whenever state changes (if active)
    useEffect(() => {
        if (isLoaded && state.assetId) {
            AsyncStorage.setItem('@cat_inspection_state', JSON.stringify(state)).catch(console.error);
        }
    }, [state, isLoaded]);

    // Global Timer for the active inspection
    useEffect(() => {
        let interval: ReturnType<typeof setInterval>;
        if (state.assetId && !state.isSubmitted && isLoaded) {
            interval = setInterval(() => {
                setState(prev => ({ ...prev, elapsedSeconds: prev.elapsedSeconds + 1, isDraft: true }));
            }, 1000);
        }
        return () => clearInterval(interval);
    }, [state.assetId, state.isSubmitted, isLoaded]);

    const updateItemStatus = (itemId: string, status: Status, timelineEstimate?: string) => {
        setState(prev => ({
            ...prev,
            itemStates: {
                ...prev.itemStates,
                [itemId]: { status, timelineEstimate }
            },
            isDraft: true,
        }));
    };

    const addNote = (itemId: string, text: string, type: 'voice' | 'text') => {
        setState(prev => ({
            ...prev,
            notes: {
                ...prev.notes,
                [itemId]: [...(prev.notes[itemId] || []), { id: Date.now().toString(), itemId, text, type, timestamp: new Date().toISOString() }]
            },
            isDraft: true,
        }));
    };

    const addPhoto = (itemId: string, uri: string) => {
        setState(prev => ({
            ...prev,
            photos: {
                ...prev.photos,
                [itemId]: [...(prev.photos[itemId] || []), { id: Date.now().toString(), itemId, uri, timestamp: new Date().toISOString() }]
            },
            isDraft: true,
        }));
    };

    const removePhoto = (itemId: string, photoId: string) => {
        setState(prev => ({
            ...prev,
            photos: {
                ...prev.photos,
                [itemId]: (prev.photos[itemId] || []).filter(p => p.id !== photoId)
            },
            isDraft: true,
        }));
    };

    const updateItemVoiceNote = (itemId: string, uri: string | null, transcript: string | null, editedTranscript: string | null = null) => {
        setState(prev => {
            const currentItem = prev.itemStates[itemId] || ({ status: null as any } as InspectionItemState);
            return {
                ...prev,
                itemStates: {
                    ...prev.itemStates,
                    [itemId]: { ...currentItem, voiceNoteUri: uri, voiceNoteTranscript: transcript, voiceNoteEditedTranscript: editedTranscript }
                },
                isDraft: true,
            };
        });
    };

    const addItemPhoto = (itemId: string, uri: string) => {
        setState(prev => {
            const currentItem = prev.itemStates[itemId] || ({ status: null as any } as InspectionItemState);
            const existingPhotos = currentItem.photos || [];
            if (existingPhotos.includes(uri)) return prev;
            return {
                ...prev,
                itemStates: {
                    ...prev.itemStates,
                    [itemId]: { ...currentItem, photos: [...existingPhotos, uri] }
                },
                isDraft: true,
            };
        });
    };

    const removeItemPhoto = (itemId: string, uri: string) => {
        setState(prev => {
            const currentItem = prev.itemStates[itemId] || ({ status: null as any } as InspectionItemState);
            const existingPhotos = currentItem.photos || [];
            return {
                ...prev,
                itemStates: {
                    ...prev.itemStates,
                    [itemId]: { ...currentItem, photos: existingPhotos.filter(p => p !== uri) }
                },
                isDraft: true,
            };
        });
    };

    const fetchAiReview = async () => {
        setState(prev => ({ ...prev, aiReviewLoading: true, aiReviewError: false }));
        try {
            // we will wire this to a service later
            const { generateAiReview } = await import('../services/aiReviewService');
            const review = await generateAiReview(state);
            setState(prev => ({ ...prev, aiReview: review, aiReviewLoading: false }));
        } catch (e) {
            console.error(e);
            setState(prev => ({ ...prev, aiReviewError: true, aiReviewLoading: false }));
        }
    };

    const submitInspection = () => {
        setState(prev => ({ ...prev, isSubmitted: true }));
        fetchAiReview();
    };

    const resetInspection = (assetId: string) => {
        const newState = { ...initialState, assetId };
        setState(newState);
        AsyncStorage.setItem('@cat_inspection_state', JSON.stringify(newState));
    };

    return (
        <InspectionContext.Provider value={{
            state, updateItemStatus, addNote, addPhoto, removePhoto, submitInspection, resetInspection,
            updateItemVoiceNote, addItemPhoto, removeItemPhoto, fetchAiReview
        }}>
            {children}
        </InspectionContext.Provider>
    );
}

export const useInspection = () => {
    const context = useContext(InspectionContext);
    if (context === undefined) {
        throw new Error('useInspection must be used within an InspectionProvider');
    }
    return context;
};
