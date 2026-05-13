import { Injectable, OnModuleInit } from '@nestjs/common';
import { createClient, ClickHouseClient } from '@clickhouse/client'
import { ConfigService } from '@nestjs/config';
@Injectable()
export class ClickhouseService implements OnModuleInit {
    constructor(private readonly configService: ConfigService) { }
    private clickhouseClient: ClickHouseClient;
    async onModuleInit() {
        this.clickhouseClient = createClient({
            url: this.configService.get('CLICKHOUSE_URL'),
            username: this.configService.get('CLICKHOUSE_USERNAME'),
            password: this.configService.get('CLICKHOUSE_PASSWORD'),
            database: this.configService.get('CLICKHOUSE_DATABASE'),
        });
        await this.clickhouseClient.command({
            query: `
        CREATE TABLE IF NOT EXISTS visitor (
            id Int64,
            anonymousId String,
            userId Nullable(String),
            browser String,
            os String,
            device String,
            createdAt DateTime,
            updatedAt DateTime
        ) ENGINE = ReplacingMergeTree(updatedAt)
         PARTITION BY toYYYYMM(createdAt)
         ORDER BY (anonymousId);
        `
        })
        await this.clickhouseClient.command({
            query: `
            CREATE TABLE IF NOT EXISTS pageView (
                id Int64,
                visitorId Int64,
                url Nullable(String),
                referrer Nullable(String),
                path Nullable(String),
                createdAt DateTime,
                updatedAt DateTime
            ) ENGINE = MergeTree
             PARTITION BY toYYYYMM(createdAt)
             ORDER BY (createdAt);
        `
        })
        await this.clickhouseClient.command({
            query: `
            CREATE TABLE IF NOT EXISTS trackEvent (
                id Int64,
                visitorId Int64,
                event String,
                payload Nullable(String),
                url String,
                createdAt DateTime,
                updatedAt DateTime
            ) ENGINE = MergeTree
             PARTITION BY toYYYYMM(createdAt)
             ORDER BY (createdAt);
        `
        })
        await this.clickhouseClient.command({
            query: `
            CREATE TABLE IF NOT EXISTS performanceEntry (
                id Int64,
                visitorId Int64,
                fp Nullable(Double),
                fcp Nullable(Double),
                lcp Nullable(Double),
                inp Nullable(Double),
                cls Nullable(Double),
                createdAt DateTime,
                updatedAt DateTime
            ) ENGINE = MergeTree
             PARTITION BY toYYYYMM(createdAt)
             ORDER BY (createdAt);
        `
        })
        await this.clickhouseClient.command({
            query: `
            CREATE TABLE IF NOT EXISTS errorEntry (
                id Int64,
                visitorId Int64,
                error Nullable(String),
                message Nullable(String),
                stack Nullable(String),
                url Nullable(String),
                createdAt DateTime,
                updatedAt DateTime
            ) ENGINE = MergeTree
             PARTITION BY toYYYYMM(createdAt)
             ORDER BY (createdAt);
        `
        })
    }
    public getClickhouseClient() {
        return this.clickhouseClient;
    }

}
