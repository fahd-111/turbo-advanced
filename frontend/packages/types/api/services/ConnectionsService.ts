/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { PaginatedSocialConnectionList } from '../models/PaginatedSocialConnectionList';
import type { SocialConnection } from '../models/SocialConnection';
import type { CancelablePromise } from '../core/CancelablePromise';
import type { BaseHttpRequest } from '../core/BaseHttpRequest';
export class ConnectionsService {
    constructor(public readonly httpRequest: BaseHttpRequest) {}
    /**
     * @param page A page number within the paginated result set.
     * @returns PaginatedSocialConnectionList
     * @throws ApiError
     */
    public connectionsList(
        page?: number,
    ): CancelablePromise<PaginatedSocialConnectionList> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/connections/',
            query: {
                'page': page,
            },
        });
    }
    /**
     * @param id A unique integer value identifying this social connection.
     * @returns SocialConnection
     * @throws ApiError
     */
    public connectionsRetrieve(
        id: number,
    ): CancelablePromise<SocialConnection> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/connections/{id}/',
            path: {
                'id': id,
            },
        });
    }
    /**
     * @param id A unique integer value identifying this social connection.
     * @returns void
     * @throws ApiError
     */
    public connectionsDestroy(
        id: number,
    ): CancelablePromise<void> {
        return this.httpRequest.request({
            method: 'DELETE',
            url: '/api/connections/{id}/',
            path: {
                'id': id,
            },
        });
    }
    /**
     * Re-read the connection's status from Composio.
     * @param id A unique integer value identifying this social connection.
     * @returns SocialConnection
     * @throws ApiError
     */
    public connectionsCheckCreate(
        id: number,
    ): CancelablePromise<SocialConnection> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/connections/{id}/check/',
            path: {
                'id': id,
            },
        });
    }
}
