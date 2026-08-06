/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Business } from '../models/Business';
import type { ConnectRequest } from '../models/ConnectRequest';
import type { ConnectResponse } from '../models/ConnectResponse';
import type { PaginatedBusinessList } from '../models/PaginatedBusinessList';
import type { PatchedBusiness } from '../models/PatchedBusiness';
import type { CancelablePromise } from '../core/CancelablePromise';
import type { BaseHttpRequest } from '../core/BaseHttpRequest';
export class BusinessesService {
    constructor(public readonly httpRequest: BaseHttpRequest) {}
    /**
     * @param page A page number within the paginated result set.
     * @returns PaginatedBusinessList
     * @throws ApiError
     */
    public businessesList(
        page?: number,
    ): CancelablePromise<PaginatedBusinessList> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/businesses/',
            query: {
                'page': page,
            },
        });
    }
    /**
     * @param requestBody
     * @returns Business
     * @throws ApiError
     */
    public businessesCreate(
        requestBody: Business,
    ): CancelablePromise<Business> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/businesses/',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param id A unique integer value identifying this business.
     * @returns Business
     * @throws ApiError
     */
    public businessesRetrieve(
        id: number,
    ): CancelablePromise<Business> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/businesses/{id}/',
            path: {
                'id': id,
            },
        });
    }
    /**
     * @param id A unique integer value identifying this business.
     * @param requestBody
     * @returns Business
     * @throws ApiError
     */
    public businessesUpdate(
        id: number,
        requestBody: Business,
    ): CancelablePromise<Business> {
        return this.httpRequest.request({
            method: 'PUT',
            url: '/api/businesses/{id}/',
            path: {
                'id': id,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param id A unique integer value identifying this business.
     * @param requestBody
     * @returns Business
     * @throws ApiError
     */
    public businessesPartialUpdate(
        id: number,
        requestBody?: PatchedBusiness,
    ): CancelablePromise<Business> {
        return this.httpRequest.request({
            method: 'PATCH',
            url: '/api/businesses/{id}/',
            path: {
                'id': id,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param id A unique integer value identifying this business.
     * @returns void
     * @throws ApiError
     */
    public businessesDestroy(
        id: number,
    ): CancelablePromise<void> {
        return this.httpRequest.request({
            method: 'DELETE',
            url: '/api/businesses/{id}/',
            path: {
                'id': id,
            },
        });
    }
    /**
     * Start the Composio OAuth flow; returns the URL to send the user to.
     * @param id A unique integer value identifying this business.
     * @param requestBody
     * @returns ConnectResponse
     * @throws ApiError
     */
    public businessesConnectCreate(
        id: number,
        requestBody: ConnectRequest,
    ): CancelablePromise<ConnectResponse> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/businesses/{id}/connect/',
            path: {
                'id': id,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
}
