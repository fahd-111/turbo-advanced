/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { PlatformEnum } from './PlatformEnum';
import type { StatusEnum } from './StatusEnum';
export type SocialConnection = {
    readonly id: number;
    readonly platform: PlatformEnum;
    readonly status: StatusEnum;
    /**
     * Instagram user id or Facebook Page id.
     */
    readonly external_account_id: string;
    readonly external_account_name: string;
    readonly is_usable: boolean;
    readonly last_checked_at: string | null;
    readonly last_error: string;
};

