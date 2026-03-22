"use client";

import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';

interface FetchState<T> {
  data: T | null;
  metadata: any | null;
  loading: boolean;
  error: string | null;
  success: boolean;
}

export function useFetch<T>(url: string | null, options: any = {}) {
  const [state, setState] = useState<FetchState<T>>({
    data: null,
    metadata: null,
    loading: !!url,
    error: null,
    success: false,
  });

  const fetchData = useCallback(async () => {
    if (!url) return;
    setState(prev => ({ ...prev, loading: true, error: null }));
    try {
      const resp = await api.get(url, options);
      const rawData = resp.data;
      const isEnvelope = rawData && typeof rawData.success === 'boolean';
      
      let finalData = isEnvelope ? rawData.data : rawData;
      
      // DRF Pagination support: if data is an object with 'results', and results is what we likely want
      if (finalData && typeof finalData === 'object' && !Array.isArray(finalData) && 'results' in finalData) {
        // If results is an array, we return it as data. 
        // If results is an object (like in our ui/transfers/), we keeping it as object but maybe we want to facilitate it.
        // For now, let's keep the results object as is if it's not a simple array.
        if (Array.isArray(finalData.results)) {
            finalData = finalData.results;
        } else {
            finalData = finalData.results;
        }
      }

      setState({
        data: finalData,
        metadata: isEnvelope ? rawData.metadata : (rawData.count !== undefined ? { count: rawData.count } : null),
        success: isEnvelope ? rawData.success : true,
        loading: false,
        error: null,
      });
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Error fetching data';
      setState({
        data: null,
        metadata: null,
        success: false,
        loading: false,
        error: msg,
      });
    }
  }, [url, JSON.stringify(options)]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { ...state, refetch: fetchData };
}
