"use client";

import { useState } from 'react';
import api from '@/lib/api';
import toast from 'react-hot-toast';

interface CRUDOptions {
  onSuccess?: (data: any) => void;
  onError?: (err: any) => void;
}

export function useCRUD(baseUrl: string) {
  const [loading, setLoading] = useState(false);

  const perform = async (
    method: 'post' | 'put' | 'patch' | 'delete',
    url: string,
    data?: any,
    options?: CRUDOptions & { multipart?: boolean }
  ) => {
    setLoading(true);
    try {
      const config = options?.multipart 
        ? { headers: { 'Content-Type': 'multipart/form-data' } }
        : {};
      
      const resp = await (api as any)[method](url, data, config);
      const resData = resp.data?.data || resp.data;
      
      options?.onSuccess?.(resData);
      return { success: true, data: resData };
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Error processing request';
      // In CRUD we often want to handle the error in the component, but we also toast it here
      options?.onError?.(err);
      return { success: false, error: msg };
    } finally {
      setLoading(false);
    }
  };

  const create = (data: any, options?: CRUDOptions & { multipart?: boolean }) => 
    perform('post', baseUrl, data, options);

  const update = (id: string, data: any, options?: CRUDOptions & { multipart?: boolean }) => 
    perform('put', `${baseUrl}${id}/`, data, options);

  const remove = (id: string, options?: CRUDOptions) => 
    perform('delete', `${baseUrl}${id}/`, null, options);

  return { create, update, remove, loading };
}
