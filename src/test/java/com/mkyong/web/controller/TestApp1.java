package com.mkyong.web.controller;

import junit.framework.Assert;
import org.junit.Test;

public class TestApp1 {

        @Test
        public void testPrintHelloWorld() {
                System.out.println("Unit Testing in Progress");
                Assert.assertEquals(HelloController.factorial(7), 5040);
                System.out.println("Unit Testing Completed" + " Factorial of 7 is " +  HelloController.factorial(7));

        }

}
