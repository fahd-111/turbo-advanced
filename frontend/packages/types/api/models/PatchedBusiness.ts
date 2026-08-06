/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { SocialConnection } from './SocialConnection';
export type PatchedBusiness = {
    readonly id?: number;
    name?: string;
    description?: string;
    industry?: string;
    website_url?: string;
    target_audience?: string;
    location?: string;
    /**
     * IANA timezone; all scheduling is rendered in this zone.
     */
    timezone?: string;
    publishing_paused?: boolean;
    replies_paused?: boolean;
    /**
     * Hours a generated post waits in the calendar before publishing.
     */
    review_buffer_hours?: number;
    /**
     * Hard cap on LLM/image spend per month.
     */
    monthly_budget_usd?: string;
    readonly connections?: Array<SocialConnection>;
    readonly created_at?: string;
};

