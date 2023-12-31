/*******************************************************************************
 * Copyright 2019 Microchip FPGA Embedded Systems Solutions.
 *
 * SPDX-License-Identifier: MIT
 *
 * @file e51.c
 * @author Microchip FPGA Embedded Systems Solutions
 * @brief Application code running on e51
 *
 */

#include <stdio.h>
#include <string.h>

#include "mpfs_hal/mss_hal.h"
#include "drivers/mss/mss_mmuart/mss_uart.h"
volatile uint32_t count_sw_ints_h0 = 0U;


#define RX_BUFF_SIZE    16U
uint8_t g_rx_buff0[RX_BUFF_SIZE] = {0};
uint8_t rx_size0 = 0U;

const uint8_t g_message1[] =
        " \r\n\r\n-------------------------------------------------------------\
--------\r\n\r\n BOOTLOADER STARTED \r\n\r\n------------------\
---------------------------------------------------\r\n";


void e51(void)
{
    volatile uint32_t icount = 0U;
    uint64_t hartid = read_csr(mhartid);

    (void) mss_config_clk_rst(MSS_PERIPH_MMUART0, (uint8_t) 1, PERIPHERAL_ON);

    MSS_UART_init(&g_mss_uart0_lo,
    MSS_UART_115200_BAUD,
    MSS_UART_DATA_8_BITS | MSS_UART_NO_PARITY | MSS_UART_ONE_STOP_BIT);

    /* Message on uart0 */
    MSS_UART_polled_tx(&g_mss_uart0_lo, g_message1, sizeof(g_message1));
}

/* hart0 software interrupt handler */
void Software_h0_IRQHandler(void)
{
    uint64_t hart_id = read_csr(mhartid);
    count_sw_ints_h0++;
}
