#!/bin/bash

# #RED
while getopts 'm:U:P:s:w:c:hp' OPT; do
  case $OPT in
    m)  MYSQL_DEFAULTS=$OPTARG;;
    U)  MYSQL_USER=$OPARG;;
    P)  MYSQL_PASS=$OPARG;;
    H)  MYSQL_HOST=$OPARG;;
    w)  WARN=$OPTARG;;
    c)  CRIT=$OPTARG;;
    s)  SCHEME=$OPTARG;;
    p)  METRICS=1;;
    h)  hlp="yes";;
    *)  unknown="yes";;
  esac
done

# usage
HELP="
    usage: $0 [ -m value -w value -c value -p -h ] or
           $0 [ -U value -H value -P value -w value -c value -p -h ]

        -m --> MySQL Defaults file
        -U --> MySQL Username
        -P --> MySQL Password
        -H --> MySQL Hostname
        -w --> Warning MB < value
        -c --> Critical MB < value
        -p --> Print metrics
        -s --> Scheme
        -h --> print this help screen
"

if [ "$hlp" = "yes" ]; then
  echo "$HELP"
  exit 0
fi

WARN=${WARN:=5}
CRIT=${CRIT:=2}
SCHEME=${SCHEME:=$(hostname -s)}

if [[ -n ${MYSQL_DEFAULTS} ]]; then
  MYSQL_CMD="mysql --defaults-file=${MYSQL_DEFAULTS} neutron -e"
elif [[ -n ${MYSQL_USER} && -n ${MYSQL_PASS} && -n ${MYSQL_HOST} ]]; then
  MYSQL_CMD="mysql -u ${MYSQL_USER} -p${MYSQL_PASS} -h ${MYSQL_HOST} neutron -e"
else
  echo "$HELP"
  exit 1
fi

if ! ${MYSQL_CMD} 'select now();' > /dev/null; then
  echo 'could not connect to mysql server'
  exit 3
fi

MYSQL_SUFFIX="'select count(id) from floatingips\G' | tail -1 | awk '{print $2}'"

TOTAL=$(${MYSQL_CMD} 'select count(id) from floatingips\G' | tail -1 | awk '{print $2}')
FREE=$(${MYSQL_CMD} 'select count(id) from floatingips where fixed_ip_address is NULL\G' | tail -1 | awk '{print $2}')
USED=$(${MYSQL_CMD} 'select count(id) from floatingips where fixed_ip_address is not NULL\G' | tail -1 | awk '{print $2}')
if [[ -n ${METRICS} ]]; then
  timestamp=$(date +%s)
  echo "${SCHEME}.fip.free ${FREE} ${timestamp}"
  echo "${SCHEME}.fip.used ${USED}  ${timestamp}"
  echo "${SCHEME}.fip.total ${TOTAL} ${timestamp}"
  exit 0
else
  if [ -z ${TOTAL} ]; then
    exit_state=2
    state_string="WARNING"
  elif [ ${FREE} -lt ${CRIT} ]; then
    exit_state=1
    state_string="CRITICAL"
  elif [ ${FREE} -lt ${WARN} ]; then
    exit_state=2
    state_string="WARNING"
  else
    exit_state=0
    state_string="OK"
  fi
  echo "${state_string} - ${FREE} available floating ip(s) out of ${TOTAL}"
  exit ${exit_state}
fi
