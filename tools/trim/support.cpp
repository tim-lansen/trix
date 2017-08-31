#include "support.h"


bool ReadFile(int file, char *buffer, DWORD number_of_bytes, DWORD *number_of_bytes_read, void *dummy)
{
    ssize_t nbr = read(file, buffer, number_of_bytes);
    if(number_of_bytes_read)
        *number_of_bytes_read = (DWORD)nbr;
    return (nbr > 0);
}

bool WriteFile(int file, const char *buffer, DWORD number_of_bytes, DWORD *number_of_bytes_written, void *dummy)
{
    ssize_t nb = write(file, buffer, number_of_bytes);
    if(number_of_bytes_written)
        *number_of_bytes_written = (DWORD)nb;
    return (nb > 0);
}