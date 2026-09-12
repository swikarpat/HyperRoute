package com.hyperroute.banking;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class BankingCoreApplication {

    public static void main(String[] args) {
        SpringApplication.run(BankingCoreApplication.class, args);
    }
}

