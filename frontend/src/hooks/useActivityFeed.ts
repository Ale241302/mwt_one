"use client";

import { useState, useEffect, useCallback, useRef } from 'react';
import api from '@/lib/api';

export interface ActivityEvent {
    event_id: string;
    event_type: string;
    action_source: string;
    previous_status: string | null;
    new_status: string | null;
    aggregate_id: string; // expediente_id
    expediente_number: string;
    proforma_id: string | null;
    proforma_number: string | null;
    user_id: number | null;
    user_display: string;
    occurred_at: string;
}

interface ActivityFeedState {
    events: ActivityEvent[];
    unreadCount: number;
    loading: boolean;
    error: string | null;
}

export function useActivityFeed(pollingInterval = 60000) {
    const [state, setState] = useState<ActivityFeedState>({
        events: [],
        unreadCount: 0,
        loading: true,
        error: null,
    });

    const isMounted = useRef(true);

    const fetchFeed = useCallback(async () => {
        try {
            const [feedRes, countRes] = await Promise.all([
                api.get('/activity-feed/'),
                api.get('/activity-feed/count/')
            ]);

            if (isMounted.current) {
                setState(prev => ({
                    ...prev,
                    events: feedRes.data.results || feedRes.data,
                    unreadCount: countRes.data.unread_count || 0,
                    loading: false,
                    error: null,
                }));
            }
        } catch (err: any) {
            if (isMounted.current) {
                setState(prev => ({
                    ...prev,
                    loading: false,
                    error: err.message || 'Error fetching activity feed',
                }));
            }
        }
    }, []);

    const markAsSeen = async () => {
        try {
            await api.post('/activity-feed/mark-seen/');
            setState(prev => ({ ...prev, unreadCount: 0 }));
        } catch (err) {
            console.error('Failed to mark activity as seen', err);
        }
    };

    useEffect(() => {
        isMounted.current = true;
        fetchFeed();

        const interval = setInterval(fetchFeed, pollingInterval);

        return () => {
            isMounted.current = false;
            clearInterval(interval);
        };
    }, [fetchFeed, pollingInterval]);

    return {
        ...state,
        markAsSeen,
        refetch: fetchFeed,
    };
}
