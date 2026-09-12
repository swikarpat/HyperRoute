# Multi-stage Dockerfile for HyperRoute Banking Core Service
FROM eclipse-temurin:21-jdk-alpine AS builder

WORKDIR /build

COPY gradlew .
COPY gradle gradle
COPY build.gradle.kts settings.gradle* ./
COPY src src

RUN chmod +x ./gradlew && ./gradlew bootJar --no-daemon

# Minimal production runtime image
FROM eclipse-temurin:21-jre-alpine AS runtime

RUN addgroup -S hyperroute && adduser -S hyperroute -G hyperroute

WORKDIR /app

COPY --from=builder /build/build/libs/*.jar app.jar
RUN chown -R hyperroute:hyperroute /app

USER hyperroute
EXPOSE 8090

ENV JAVA_OPTS="-XX:+UseZGC -XX:+ZGenerational -Xms256m -Xmx512m"

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
